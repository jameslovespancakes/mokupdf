"""
Allow running mokupdf as a module: python -m mokupdf
"""

from .server import main

if __name__ == "__main__":
    main()