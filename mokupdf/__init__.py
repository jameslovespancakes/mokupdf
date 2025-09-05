"""
MokuPDF - MCP-compatible PDF reading server
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .server import main, PDFProcessor

__all__ = ["main", "PDFProcessor", "__version__"]