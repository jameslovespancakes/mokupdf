# MokuPDF - Intelligent PDF Reading Server for AI

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/mokupdf.svg)](https://badge.fury.io/py/mokupdf)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

MokuPDF is a powerful, MCP (Model Context Protocol) compatible server that enables AI applications to read and process PDF files with advanced capabilities. It combines intelligent file search, comprehensive text extraction, image processing, and optional OCR support to handle any type of PDF document - from simple text files to complex scanned documents.

> 🚀 **Perfect for Claude Desktop, ChatGPT plugins, and any AI application that needs PDF processing capabilities!**

## 📋 Table of Contents

- [✨ Key Features](#-key-features)
- [📦 Installation](#-installation)
- [🎯 Quick Start](#-quick-start)
- [🔧 MCP Configuration](#-mcp-configuration)  
- [📚 Available Tools](#-available-tools)
- [💡 Usage Examples](#-usage-examples)
- [🖼️ Image & Scanned PDF Support](#️-image--scanned-pdf-support)
- [🔍 Smart File Search](#-smart-file-search)
- [⚙️ Configuration Options](#️-configuration-options)
- [🛠️ Development](#️-development)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## ✨ Key Features

### 🔍 **Intelligent PDF Processing**
- **📄 Full Text Extraction** - Extract all text content from any PDF
- **🖼️ Advanced Image Handling** - Extract embedded images as base64 PNG with proper format conversion  
- **📱 Scanned PDF Support** - Auto-detects and renders image-based/scanned PDFs at high resolution
- **🔤 Optional OCR Integration** - Extract text from scanned documents using Tesseract (optional)
- **📑 Page-by-Page Processing** - Handle large PDFs efficiently without memory issues

### 🎯 **Smart File Operations** 
- **🧠 Intelligent File Search** - Find PDFs using natural language: "find the report", "open invoice"
- **📍 Multi-Location Search** - Automatically searches Desktop, Downloads, Documents, and OneDrive
- **🔗 Fuzzy Matching** - Handles typos and partial filenames intelligently
- **🔍 Advanced Text Search** - Search within PDFs with regex support and context

### 🤖 **AI Integration**
- **⚡ MCP Protocol Compliant** - Seamlessly integrates with Claude Desktop and other AI tools
- **🔌 FastMCP Architecture** - Built on the official MCP Python SDK for reliability
- **📡 JSON-RPC Interface** - Clean, standardized API for easy integration
- **⚙️ Configurable & Lightweight** - Minimal dependencies, fast startup, customizable options

## 📦 Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/mokupdf.git
cd mokupdf

# Install the package
pip install .

# Or install in development mode
pip install -e .
```

### Using pip (when published)

```bash
# Basic installation
pip install mokupdf

# With OCR support for scanned PDFs
pip install mokupdf[ocr]
```

**Note**: For OCR functionality, you'll also need Tesseract installed on your system:
- **Windows**: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
- **Mac**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

## 🎯 Quick Start

### Running the Server

```bash
# Start with default settings (port 8000)
mokupdf

# Start with custom port
mokupdf --port 8080

# Enable verbose logging
mokupdf --verbose

# Set custom PDF directory
mokupdf --base-dir ./documents
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--port` | Port to listen on | 8000 |
| `--verbose` | Enable verbose logging | False |
| `--base-dir` | Base directory for PDF files | Current directory |
| `--max-file-size` | Maximum PDF file size in MB | 100 |
| `--version` | Show version information | - |
| `--help` | Show help message | - |

## 🔧 MCP Configuration

Add MokuPDF to your MCP configuration file:

```json
{
  "mcpServers": {
    "mokupdf": {
      "command": "python",
      "args": ["-m", "mokupdf", "--port", "8000"],
      "name": "MokuPDF",
      "description": "PDF reading server with text and image extraction",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## 📚 Available MCP Tools

### 1. open_pdf
Open a PDF file for processing.

```json
{
  "tool": "open_pdf",
  "arguments": {
    "file_path": "document.pdf"
  }
}
```

### 2. read_pdf
Read PDF pages with text and images. Supports page ranges for efficient processing.

```json
{
  "tool": "read_pdf",
  "arguments": {
    "file_path": "document.pdf",
    "start_page": 1,
    "end_page": 5,
    "max_pages": 10
  }
}
```

**Response includes:**
- Text content with `[IMAGE: ...]` placeholders
- Base64-encoded images
- Page information

### 3. search_text
Search for text within the current PDF.

```json
{
  "tool": "search_text",
  "arguments": {
    "query": "introduction",
    "case_sensitive": false
  }
}
```

### 4. get_page_text
Extract text from a specific page.

```json
{
  "tool": "get_page_text",
  "arguments": {
    "page_number": 1
  }
}
```

### 5. get_metadata
Get metadata from the current PDF.

```json
{
  "tool": "get_metadata",
  "arguments": {}
}
```

### 6. close_pdf
Close the current PDF and free memory.

```json
{
  "tool": "close_pdf", 
  "arguments": {}
}
```

### 7. find_pdf_files
Find PDF files using intelligent search across common directories.

```json
{
  "tool": "find_pdf_files",
  "arguments": {
    "query": "financial report",
    "limit": 5
  }
}
```

## 💡 Usage Examples

### 🎯 **Natural Language File Access**
```bash
# Instead of exact paths, use natural language
User: "Can you read the financial report from last quarter?"
Claude: Uses find_pdf_files("financial report") → Opens Q3_Financial_Report.pdf

User: "Look at the user manual on my desktop"  
Claude: Searches Desktop → Finds User_Manual_v2.pdf → Processes it

User: "Find all invoices"
Claude: Returns list of all PDFs containing "invoice" from common locations
```

### 📄 **Text-Based PDFs**
```python
# Regular PDF with embedded images
{
  "tool": "read_pdf",
  "arguments": {
    "file_path": "annual_report.pdf",
    "start_page": 1,
    "max_pages": 10
  }
}

# Response includes:
# - Extracted text content
# - Image placeholders: [IMAGE: Image 1 - 800x600px]  
# - Base64-encoded images array
# - Page metadata
```

### 🖼️ **Scanned PDFs (Image-Based)**
```python
# Scanned document without OCR
{
  "tool": "read_pdf",
  "arguments": {
    "file_path": "scanned_contract.pdf"
  }
}

# Response:
# - "[SCANNED PAGE: This page appears to be a scanned image]"
# - "[IMAGE: Full Page Scan - 1654x2339px]"
# - High-resolution page image as base64

# With OCR enabled (pip install mokupdf[ocr])
# Response:
# - "[SCANNED PAGE - OCR EXTRACTED TEXT]:"  
# - "Actual extracted text content..."
# - "[IMAGE: Full Page Scan - 1654x2339px]"
# - Original page image as base64
```

### 🔍 **Smart Search & Discovery**
```python
# Find files by content or name
{
  "tool": "find_pdf_files", 
  "arguments": {
    "query": "invoice 2024",
    "limit": 5
  }
}

# Response includes:
# - Ranked list of matching files
# - File metadata (size, modification date, location)
# - Relevance scores
```

## 🖼️ Image & Scanned PDF Support

MokuPDF automatically handles different PDF types:

| PDF Type | Text Extraction | Image Handling | OCR Support |
|----------|----------------|----------------|-------------|
| **Text-based PDF** | ✅ Direct extraction | ✅ Embedded images extracted | ➖ Not needed |
| **Mixed PDF** | ✅ Text + images | ✅ All images extracted | ➖ Not needed |  
| **Scanned PDF** | ⚠️ Limited/None | ✅ Full page rendered | ✅ Optional OCR |
| **Image-only PDF** | ➖ None | ✅ Full page rendered | ✅ Optional OCR |

### OCR Installation
```bash
# Install with OCR support
pip install mokupdf[ocr]

# Install Tesseract system dependency
# Windows: Download from GitHub releases
# Mac: brew install tesseract  
# Linux: sudo apt-get install tesseract-ocr
```

## 🔍 Smart File Search

MokuPDF's intelligent file finder works with natural language:

### **Search Patterns**
- **Exact matches**: `"report"` → `Annual_Report.pdf`
- **Partial matches**: `"ann"` → `Annual_Report.pdf`
- **Multiple terms**: `"financial report 2024"` → `Financial_Report_2024.pdf`
- **Fuzzy matching**: `"finacial"` → `Financial_Report.pdf` (handles typos)

### **Search Locations**
- Current working directory
- `~/Desktop`
- `~/Downloads` 
- `~/Documents`
- `~/OneDrive/Desktop` (if available)
- `~/OneDrive/Documents` (if available)

### **Ranking System**
Files are ranked by:
- **Exact name matches** (highest priority)
- **Word boundary matches**
- **Partial string matches** 
- **Recent modification time** (boost for recent files)
- **File location** (Desktop files prioritized)

## ⚙️ Configuration Options

### **Command Line Arguments**
```bash
mokupdf --help

Options:
  --base-dir PATH        Base directory for PDF files (default: current)
  --max-file-size INT    Maximum PDF size in MB (default: 100)
  --port INT            Port number (legacy, ignored by FastMCP)
  --verbose             Enable verbose logging (legacy, ignored)
  --version             Show version information
```

### **MCP Server Configuration**
```json
{
  "mcpServers": {
    "mokupdf": {
      "command": "python",
      "args": ["-m", "mokupdf", "--base-dir", "./documents", "--max-file-size", "200"],
      "name": "MokuPDF",
      "description": "Advanced PDF processing with smart search and OCR"
    }
  }
}
```

## 💻 Development

### Project Structure

```
mokupdf/
├── mokupdf/
│   ├── __init__.py       # Package initialization
│   ├── server.py         # Main server implementation
│   └── __main__.py       # Module entry point
├── setup.py              # Package setup script
├── pyproject.toml        # Modern Python packaging
├── requirements.txt      # Direct dependencies
├── LICENSE              # MIT License
└── README.md           # This file
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=mokupdf
```

### Code Quality

```bash
# Format code
black mokupdf/

# Lint code  
flake8 mokupdf/
```

### **Architecture**

MokuPDF is built using:
- **FastMCP**: Official MCP Python SDK for reliable protocol handling
- **PyMuPDF (fitz)**: High-performance PDF processing and rendering
- **Pillow**: Image format conversion and processing
- **pytesseract**: Optional OCR text extraction from scanned documents

## 🛠️ Troubleshooting

### **Common Issues**

**🔸 "ModuleNotFoundError: No module named 'mokupdf'"**
```bash
# Install the package
pip install mokupdf
```

**🔸 "No PDF is currently open"** 
```bash
# Always open a PDF first, or provide file_path in read_pdf
{
  "tool": "open_pdf",
  "arguments": {"file_path": "document.pdf"}
}
```

**🔸 "PDF file not found"**
```bash 
# Use smart search instead of exact paths
{
  "tool": "find_pdf_files",
  "arguments": {"query": "document"}
}
```

**🔸 OCR not working**
```bash
# Install OCR dependencies
pip install mokupdf[ocr]

# Windows: Download Tesseract from GitHub releases
# Mac: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr  
```

**🔸 "File too large" errors**
```bash  
# Increase file size limit
mokupdf --max-file-size 500  # Allow 500MB files
```

### **Debug Mode**
```bash
# Enable verbose logging for detailed information
mokupdf --verbose

# Check MCP connection in Claude Desktop developer tools
# Press Ctrl+Shift+I in Claude Desktop
```

## 📈 Performance Tips

- **Large PDFs**: Use `start_page` and `end_page` parameters for chunked processing
- **Memory usage**: Close PDFs when done with `close_pdf` tool  
- **OCR speed**: OCR processing adds significant time - disable if not needed
- **File search**: Search is cached - repeated searches are faster
- **Image quality**: Scanned pages rendered at 2x resolution for clarity

## 🗺️ Roadmap

- [ ] **Advanced OCR**: Multiple language support, confidence scores
- [ ] **Enhanced Search**: Content-based PDF search (search inside PDF text)
- [ ] **Batch Processing**: Process multiple PDFs simultaneously  
- [ ] **Format Support**: Add support for other document formats (DOCX, PPTX)
- [ ] **Cloud Integration**: Support for cloud storage (Google Drive, OneDrive API)
- [ ] **Performance**: Async processing for better concurrent handling

## 🔍 Example Usage

### Python Script Example

```python
import json
import subprocess

# Start MokuPDF server
process = subprocess.Popen(
    ["mokupdf", "--port", "8000"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Send a request to open a PDF
request = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "open_pdf",
        "arguments": {"file_path": "example.pdf"}
    },
    "id": 1
}

# Send request
process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()

# Read response
response = json.loads(process.stdout.readline())
print(f"PDF opened: {response['result']}")
```

### Integration with LLMs

MokuPDF is designed to work seamlessly with LLM applications through MCP. The `read_pdf` tool returns content in a format optimized for LLM consumption:

1. Text is extracted with page markers
2. Images are embedded as base64 PNG with placeholders in text
3. Large PDFs can be read page-by-page to avoid context limits

## 🛠️ Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'mokupdf'`
- **Solution**: Install the package with `pip install .`

**Issue**: Port already in use
- **Solution**: Use a different port with `--port 8081`

**Issue**: PDF file not found
- **Solution**: Check the base directory and ensure paths are relative to it

**Issue**: Large PDF causes timeout
- **Solution**: Use page-by-page reading with `start_page` and `end_page` parameters

### Debug Mode

Enable verbose logging for detailed information:

```bash
mokupdf --verbose
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! MokuPDF is designed to be the best PDF processing tool for AI applications.

### **How to Contribute**

1. **🍴 Fork the repository**
2. **🌿 Create a feature branch**: `git checkout -b feature/amazing-feature`  
3. **📝 Make your changes** with clear, documented code
4. **✅ Add tests** for new functionality
5. **🧹 Run code formatting**: `black mokupdf/`
6. **✨ Submit a pull request**

### **Development Setup**
```bash
# Clone your fork
git clone https://github.com/yourusername/mokupdf.git
cd mokupdf

# Install in development mode with all dependencies  
pip install -e ".[dev,ocr]"

# Run tests
pytest

# Format code
black mokupdf/
flake8 mokupdf/
```

### **Contribution Ideas**
- 🌍 **Multi-language OCR support**
- ⚡ **Performance optimizations** 
- 🔍 **Advanced search algorithms**
- 📱 **New document format support**
- 🐛 **Bug fixes and improvements**
- 📚 **Documentation enhancements**

## 📞 Support & Community

### **Getting Help**
- 📝 **Issues**: [Open a GitHub issue](https://github.com/mokupdf/mokupdf/issues) for bugs or feature requests
- 💬 **Discussions**: Use GitHub Discussions for questions and community support
- 🔧 **Troubleshooting**: Enable `--verbose` mode for detailed debugging information

### **Reporting Bugs**
When reporting issues, please include:
- Operating system and Python version
- MokuPDF version (`mokupdf --version`)
- Sample PDF file (if possible)
- Complete error message and traceback
- Steps to reproduce the issue

## 🙏 Acknowledgments

MokuPDF is built on the shoulders of giants:

- **[PyMuPDF](https://pymupdf.readthedocs.io/)** - Exceptional PDF processing and rendering capabilities
- **[FastMCP](https://modelcontextprotocol.io/)** - Official MCP Python SDK for reliable protocol handling  
- **[Tesseract OCR](https://github.com/tesseract-ocr/tesseract)** - Open-source OCR engine for text extraction
- **[Pillow](https://pillow.readthedocs.io/)** - Python Imaging Library for image processing
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - Standardized protocol for AI tool integration

Special thanks to the AI and open-source communities for inspiration and feedback.

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### **MIT License Summary**
- ✅ **Commercial use** - Use in commercial applications
- ✅ **Modification** - Modify and distribute changes
- ✅ **Distribution** - Distribute original or modified versions
- ✅ **Private use** - Use privately without restrictions
- ❌ **No warranty** - Software provided "as-is"
- ⚖️ **License notice** - Include original license in copies

---

<div align="center">

**🚀 Made with ❤️ for the AI community**

[![PyPI](https://img.shields.io/pypi/v/mokupdf.svg)](https://pypi.org/project/mokupdf/)
[![Downloads](https://pepy.tech/badge/mokupdf)](https://pepy.tech/project/mokupdf)
[![GitHub stars](https://img.shields.io/github/stars/mokupdf/mokupdf.svg?style=social)](https://github.com/mokupdf/mokupdf)

**[⭐ Star us on GitHub](https://github.com/mokupdf/mokupdf) • [📦 Install from PyPI](https://pypi.org/project/mokupdf/) • [📚 Read the Docs](https://github.com/mokupdf/mokupdf#readme)**

</div>
