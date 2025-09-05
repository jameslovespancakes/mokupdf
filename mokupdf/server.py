#!/usr/bin/env python3
"""
MokuPDF - MCP-compatible PDF reading server

A lightweight, MCP (Model Context Protocol) compatible server that enables LLMs to read and process
PDF files with full text and image extraction capabilities.
"""

import argparse
import base64
import io
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

try:
    from mcp.server.fastmcp import FastMCP
    import fitz  # PyMuPDF
    from PIL import Image
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install with: pip install mcp>=1.2.0 PyMuPDF>=1.23.0 Pillow>=10.0.0")
    sys.exit(1)

# Optional OCR support
try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


__version__ = "1.0.0"


class SmartFileFinder:
    """Intelligent file finder that can locate PDFs based on partial names or descriptions"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).resolve()
        self.common_locations = self._get_common_locations()
    
    def _get_common_locations(self) -> List[Path]:
        """Get common locations to search for files"""
        locations = [self.base_dir]
        
        # Add user's common directories
        home = Path.home()
        common_dirs = [
            home / "Desktop",
            home / "Downloads", 
            home / "Documents",
            home / "OneDrive" / "Desktop" if (home / "OneDrive" / "Desktop").exists() else None,
            home / "OneDrive" / "Documents" if (home / "OneDrive" / "Documents").exists() else None,
        ]
        
        # Filter out None values and add existing directories
        for dir_path in common_dirs:
            if dir_path and dir_path.exists() and dir_path.is_dir():
                locations.append(dir_path)
        
        return locations
    
    def find_pdf_files(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find PDF files based on a search query
        
        Args:
            query: Search query (can be partial filename, keywords, etc.)
            limit: Maximum number of results to return
            
        Returns:
            List of matching PDF files with metadata
        """
        if not query.strip():
            return []
        
        # Clean and prepare search terms
        search_terms = self._extract_search_terms(query.lower())
        all_matches = []
        
        # Search in all common locations
        for location in self.common_locations:
            try:
                matches = self._search_in_directory(location, search_terms)
                all_matches.extend(matches)
            except (PermissionError, OSError):
                # Skip directories we can't access
                continue
        
        # Remove duplicates and sort by relevance
        unique_matches = self._deduplicate_matches(all_matches)
        sorted_matches = self._score_and_sort_matches(unique_matches, search_terms)
        
        return sorted_matches[:limit]
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract meaningful search terms from query"""
        # Remove common words and split into terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that', 'look', 'find', 'open', 'read', 'pdf', 'file', 'document'}
        
        # Split on spaces and punctuation, keep alphanumeric
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out stop words and short words
        search_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        # If no meaningful terms, use original query
        if not search_terms:
            search_terms = [query.strip()]
        
        return search_terms
    
    def _search_in_directory(self, directory: Path, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Search for PDF files in a specific directory"""
        matches = []
        
        try:
            # Search PDF files in directory (not recursive to avoid performance issues)
            for pdf_file in directory.glob("*.pdf"):
                if not pdf_file.is_file():
                    continue
                
                # Calculate relevance score
                filename_lower = pdf_file.stem.lower()
                score = self._calculate_match_score(filename_lower, search_terms)
                
                if score > 0:
                    # Get file metadata
                    stat = pdf_file.stat()
                    match_info = {
                        "file_path": str(pdf_file),
                        "filename": pdf_file.name,
                        "directory": str(pdf_file.parent),
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified_time": stat.st_mtime,
                        "score": score
                    }
                    matches.append(match_info)
        
        except (PermissionError, OSError):
            pass
        
        return matches
    
    def _calculate_match_score(self, filename: str, search_terms: List[str]) -> int:
        """Calculate relevance score for a filename"""
        score = 0
        
        for term in search_terms:
            if term in filename:
                # Exact substring match
                score += 10
                
                # Bonus for word boundary matches
                if re.search(r'\b' + re.escape(term) + r'\b', filename):
                    score += 5
                
                # Bonus for beginning of filename
                if filename.startswith(term):
                    score += 3
        
        # Fuzzy matching for typos (simple)
        for term in search_terms:
            if len(term) > 4:  # Only for longer terms
                for word in filename.split('_'):  # Common separator
                    if self._fuzzy_match(term, word):
                        score += 3
        
        return score
    
    def _fuzzy_match(self, term: str, word: str) -> bool:
        """Simple fuzzy matching for typos"""
        if len(word) < 3 or abs(len(term) - len(word)) > 2:
            return False
        
        # Simple edit distance check (very basic)
        if len(set(term) & set(word)) >= min(len(term), len(word)) * 0.7:
            return True
        
        return False
    
    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate files (same file found in different searches)"""
        seen_files = set()
        unique_matches = []
        
        for match in matches:
            file_path = match["file_path"]
            if file_path not in seen_files:
                seen_files.add(file_path)
                unique_matches.append(match)
        
        return unique_matches
    
    def _score_and_sort_matches(self, matches: List[Dict[str, Any]], search_terms: List[str]) -> List[Dict[str, Any]]:
        """Sort matches by relevance score and recency"""
        for match in matches:
            # Boost score for recently modified files
            recency_boost = min(5, int((match["modified_time"] - 1640995200) / (86400 * 30)))  # Boost for recent months
            match["final_score"] = match["score"] + recency_boost
        
        # Sort by score (desc), then by modification time (desc)
        return sorted(matches, key=lambda x: (x["final_score"], x["modified_time"]), reverse=True)


class PDFProcessor:
    """Handles PDF processing operations"""
    
    def __init__(self, base_dir: str = ".", max_file_size_mb: int = 100):
        self.base_dir = Path(base_dir).resolve()
        self.max_file_size_mb = max_file_size_mb
        self.current_pdf = None
        self.current_pdf_path = None
        self.file_finder = SmartFileFinder(base_dir)
        
    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path relative to base directory or find via smart search"""
        path = Path(file_path)
        
        # If it's an absolute path or exists relative to base_dir, use it directly
        if path.is_absolute():
            return path.resolve()
        
        # Try relative to base_dir first
        relative_path = self.base_dir / path
        if relative_path.exists():
            return relative_path.resolve()
        
        # If file doesn't exist, try smart file finding
        search_results = self.file_finder.find_pdf_files(file_path, limit=1)
        if search_results:
            # Use the best match
            found_path = Path(search_results[0]["file_path"])
            return found_path
        
        # Fallback to original behavior
        return relative_path.resolve()
        
    def _check_file_size(self, file_path: Path) -> None:
        """Check if file size is within limits"""
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise ValueError(f"File size ({file_size_mb:.1f}MB) exceeds limit ({self.max_file_size_mb}MB)")
            
    def open_pdf(self, file_path: str) -> Dict[str, Any]:
        """Open a PDF file for processing"""
        try:
            original_input = file_path
            path = self._resolve_path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"PDF file not found: {path}")
                
            if not path.suffix.lower() == '.pdf':
                raise ValueError(f"File is not a PDF: {path}")
                
            self._check_file_size(path)
            
            # Close existing PDF if open
            if self.current_pdf:
                self.current_pdf.close()
                
            # Open new PDF
            self.current_pdf = fitz.open(str(path))
            self.current_pdf_path = str(path)
            
            # Check if we found the file via smart search
            found_via_search = str(path) != str(Path(original_input).resolve()) and not Path(original_input).exists()
            
            message = f"PDF opened successfully: {path.name}"
            if found_via_search:
                message += f" (found via search for '{original_input}')"
            
            return {
                "success": True,
                "file_path": str(path),
                "original_query": original_input if found_via_search else None,
                "found_via_search": found_via_search,
                "pages": len(self.current_pdf),
                "message": message
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to open PDF: {file_path}"
            }
    
    def _extract_page_images(self, page) -> List[Dict[str, Any]]:
        """Extract images from a page and return as base64 encoded data"""
        images = []
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                pix = fitz.Pixmap(self.current_pdf, xref)
                
                # Convert to PNG if not already
                if pix.n - pix.alpha < 4:  # Gray or RGB
                    img_data = pix.tobytes("png")
                else:  # CMYK: convert via PIL
                    pil_img = Image.frombytes("CMYK", [pix.width, pix.height], pix.samples)
                    pil_img = pil_img.convert("RGB")
                    img_buffer = io.BytesIO()
                    pil_img.save(img_buffer, format="PNG")
                    img_data = img_buffer.getvalue()
                
                # Encode as base64
                base64_data = base64.b64encode(img_data).decode('utf-8')
                
                images.append({
                    "index": img_index,
                    "format": "png",
                    "base64": base64_data,
                    "width": pix.width,
                    "height": pix.height
                })
                
                pix = None  # Clean up
                
            except Exception as e:
                print(f"Error extracting image {img_index}: {e}", file=sys.stderr)
                
        return images
    
    def read_pdf(self, file_path: Optional[str] = None, start_page: int = 1, 
                end_page: Optional[int] = None, max_pages: int = 50) -> Dict[str, Any]:
        """Read PDF pages with text and image extraction"""
        try:
            # Open PDF if file_path provided and different from current
            if file_path and file_path != self.current_pdf_path:
                result = self.open_pdf(file_path)
                if not result["success"]:
                    return result
            
            if not self.current_pdf:
                return {
                    "success": False,
                    "error": "No PDF is currently open",
                    "message": "Use open_pdf first or provide a file_path"
                }
            
            total_pages = len(self.current_pdf)
            
            # Validate and adjust page ranges
            start_page = max(1, start_page)
            if end_page is None:
                end_page = min(total_pages, start_page + max_pages - 1)
            else:
                end_page = min(total_pages, end_page)
            
            if start_page > total_pages:
                return {
                    "success": False,
                    "error": f"Start page {start_page} exceeds total pages {total_pages}",
                    "message": "Invalid page range"
                }
            
            # Process pages
            pages_data = []
            all_images = []
            
            for page_num in range(start_page - 1, end_page):  # Convert to 0-indexed
                page = self.current_pdf[page_num]
                
                # Extract text
                text = page.get_text()
                
                # Extract embedded images
                page_images = self._extract_page_images(page)
                
                # Check if this is an image-based page (scanned PDF)
                is_image_based = len(text.strip()) < 10 and len(page_images) == 0
                
                if is_image_based:
                    # Render entire page as image for scanned PDFs
                    try:
                        # Use 2x resolution for better quality
                        mat = fitz.Matrix(2, 2)
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        
                        # Create full-page image entry
                        page_image = {
                            "index": 0,
                            "format": "png", 
                            "base64": img_base64,
                            "width": pix.width,
                            "height": pix.height,
                            "type": "full_page"
                        }
                        page_images.append(page_image)
                        
                        # Try to extract text via OCR if available
                        ocr_text = ""
                        if HAS_OCR:
                            try:
                                # Convert pixmap to PIL Image for OCR
                                pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                                ocr_text = pytesseract.image_to_string(pil_image, config='--psm 6')
                                ocr_text = ocr_text.strip()
                            except Exception as e:
                                print(f"OCR failed for page {page_num + 1}: {e}", file=sys.stderr)
                        
                        # Set text content
                        if ocr_text:
                            processed_text = f"[SCANNED PAGE - OCR EXTRACTED TEXT]:\n\n{ocr_text}\n\n[IMAGE: Full Page Scan - {pix.width}x{pix.height}px]"
                        else:
                            ocr_status = " (OCR not available - install pytesseract for text extraction)" if not HAS_OCR else " (OCR found no text)"
                            processed_text = f"[SCANNED PAGE: This page appears to be a scanned image{ocr_status}]\n\n[IMAGE: Full Page Scan - {pix.width}x{pix.height}px]"
                        
                        pix = None  # Clean up
                        
                    except Exception as e:
                        print(f"Error rendering page {page_num + 1} as image: {e}", file=sys.stderr)
                        processed_text = text if text.strip() else "[EMPTY PAGE: No text or images found]"
                
                else:
                    # Regular PDF with text - add image placeholders
                    processed_text = text
                    for i, img in enumerate(page_images):
                        placeholder = f"[IMAGE: Image {len(all_images) + i + 1} - {img['width']}x{img['height']}px]"
                        # Simple placeholder insertion - could be improved with position detection
                        if i == 0:
                            processed_text = processed_text + "\n\n" + placeholder
                        else:
                            processed_text = processed_text + "\n" + placeholder
                
                pages_data.append({
                    "page": page_num + 1,
                    "text": processed_text,
                    "image_count": len(page_images),
                    "is_image_based": is_image_based
                })
                
                # Add images to global list
                all_images.extend(page_images)
            
            return {
                "success": True,
                "file_path": self.current_pdf_path,
                "pages_read": len(pages_data),
                "total_pages": total_pages,
                "start_page": start_page,
                "end_page": end_page,
                "pages": pages_data,
                "images": all_images,
                "message": f"Successfully read {len(pages_data)} pages"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to read PDF pages"
            }
    
    def search_text(self, query: str, case_sensitive: bool = False) -> Dict[str, Any]:
        """Search for text within the current PDF"""
        try:
            if not self.current_pdf:
                return {
                    "success": False,
                    "error": "No PDF is currently open",
                    "message": "Use open_pdf first"
                }
            
            results = []
            flags = 0 if case_sensitive else fitz.TEXT_DEHYPHENATE
            
            for page_num in range(len(self.current_pdf)):
                page = self.current_pdf[page_num]
                text_instances = page.search_for(query, flags=flags)
                
                if text_instances:
                    page_text = page.get_text()
                    for inst in text_instances:
                        # Get surrounding context
                        words = page_text.split()
                        query_words = query.split()
                        
                        # Find approximate position for context
                        context_start = max(0, len(words) // 2 - 10)
                        context_end = min(len(words), context_start + 20)
                        context = " ".join(words[context_start:context_end])
                        
                        results.append({
                            "page": page_num + 1,
                            "bbox": list(inst),  # Bounding box coordinates
                            "context": context
                        })
            
            return {
                "success": True,
                "query": query,
                "case_sensitive": case_sensitive,
                "matches_found": len(results),
                "results": results,
                "message": f"Found {len(results)} matches for '{query}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to search for text: {query}"
            }
    
    def get_page_text(self, page_number: int) -> Dict[str, Any]:
        """Extract text from a specific page"""
        try:
            if not self.current_pdf:
                return {
                    "success": False,
                    "error": "No PDF is currently open",
                    "message": "Use open_pdf first"
                }
            
            if page_number < 1 or page_number > len(self.current_pdf):
                return {
                    "success": False,
                    "error": f"Page {page_number} out of range (1-{len(self.current_pdf)})",
                    "message": "Invalid page number"
                }
            
            page = self.current_pdf[page_number - 1]  # Convert to 0-indexed
            text = page.get_text()
            
            return {
                "success": True,
                "page": page_number,
                "text": text,
                "message": f"Successfully extracted text from page {page_number}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to extract text from page {page_number}"
            }
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata from the current PDF"""
        try:
            if not self.current_pdf:
                return {
                    "success": False,
                    "error": "No PDF is currently open",
                    "message": "Use open_pdf first"
                }
            
            metadata = self.current_pdf.metadata
            
            return {
                "success": True,
                "file_path": self.current_pdf_path,
                "pages": len(self.current_pdf),
                "metadata": {
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "subject": metadata.get("subject", ""),
                    "creator": metadata.get("creator", ""),
                    "producer": metadata.get("producer", ""),
                    "created": metadata.get("creationDate", ""),
                    "modified": metadata.get("modDate", ""),
                    "encrypted": self.current_pdf.is_encrypted,
                    "page_count": len(self.current_pdf)
                },
                "message": "Successfully retrieved PDF metadata"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve PDF metadata"
            }
    
    def close_pdf(self) -> Dict[str, Any]:
        """Close the current PDF and free memory"""
        try:
            if self.current_pdf:
                self.current_pdf.close()
                file_path = self.current_pdf_path
                self.current_pdf = None
                self.current_pdf_path = None
                
                return {
                    "success": True,
                    "message": f"PDF closed: {file_path}"
                }
            else:
                return {
                    "success": True,
                    "message": "No PDF was open"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to close PDF"
            }

def create_mcp_server(base_dir: str = ".", max_file_size_mb: int = 100) -> FastMCP:
    """Create and configure the MCP server with PDF tools"""
    
    mcp = FastMCP("MokuPDF")
    pdf_processor = PDFProcessor(base_dir, max_file_size_mb)
    
    @mcp.tool()
    def find_pdf_files(query: str, limit: int = 10) -> Dict[str, Any]:
        """Find PDF files based on a search query (partial filename, keywords, etc.)
        
        Args:
            query: Search terms to find PDF files (e.g., "report", "invoice", "manual")
            limit: Maximum number of results to return (default: 10)
            
        Returns:
            Dict containing list of matching PDF files with metadata
        """
        try:
            matches = pdf_processor.file_finder.find_pdf_files(query, limit)
            
            return {
                "success": True,
                "query": query,
                "matches_found": len(matches),
                "files": matches,
                "message": f"Found {len(matches)} PDF files matching '{query}'"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to search for PDF files: {query}"
            }
    
    @mcp.tool()
    def open_pdf(file_path: str) -> Dict[str, Any]:
        """Open a PDF file for processing (supports smart file finding)
        
        Args:
            file_path: Path to PDF file or search terms to find the file
            
        Returns:
            Dict containing success status, file info, and message
        """
        return pdf_processor.open_pdf(file_path)
    
    @mcp.tool()
    def read_pdf(file_path: Optional[str] = None, start_page: int = 1, 
                end_page: Optional[int] = None, max_pages: int = 50) -> Dict[str, Any]:
        """Read PDF pages with text and image extraction (supports smart file finding)
        
        Args:
            file_path: Path to PDF file or search terms to find the file (optional if already open)
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (optional)
            max_pages: Maximum number of pages to read
            
        Returns:
            Dict containing text content, images as base64, and page information
        """
        return pdf_processor.read_pdf(file_path, start_page, end_page, max_pages)
    
    @mcp.tool()
    def search_text(query: str, case_sensitive: bool = False) -> Dict[str, Any]:
        """Search for text within the current PDF
        
        Args:
            query: Text to search for
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            Dict containing search results with page numbers and context
        """
        return pdf_processor.search_text(query, case_sensitive)
    
    @mcp.tool()
    def get_page_text(page_number: int) -> Dict[str, Any]:
        """Extract text from a specific page
        
        Args:
            page_number: Page number to extract text from (1-indexed)
            
        Returns:
            Dict containing the extracted text
        """
        return pdf_processor.get_page_text(page_number)
    
    @mcp.tool()
    def get_metadata() -> Dict[str, Any]:
        """Get metadata from the current PDF
        
        Returns:
            Dict containing PDF metadata information
        """
        return pdf_processor.get_metadata()
    
    @mcp.tool()
    def close_pdf() -> Dict[str, Any]:
        """Close the current PDF and free memory
        
        Returns:
            Dict containing success status and message
        """
        return pdf_processor.close_pdf()
    
    return mcp


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        prog="mokupdf",
        description="MCP-compatible PDF reading server with text and image extraction"
    )
    
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base directory for PDF files (default: current directory)"
    )
    
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=100,
        help="Maximum PDF file size in MB (default: 100)"
    )
    
    # Legacy arguments for MCP compatibility (ignored)
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number (ignored with FastMCP, kept for compatibility)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (ignored with FastMCP, kept for compatibility)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"MokuPDF {__version__}"
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    try:
        args = parse_args()
        
        # Create and run the MCP server
        mcp = create_mcp_server(
            base_dir=args.base_dir,
            max_file_size_mb=args.max_file_size
        )
        
        mcp.run()
        
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()