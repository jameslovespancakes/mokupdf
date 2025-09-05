#!/usr/bin/env python3
"""
Setup script for MokuPDF - MCP-compatible PDF reading server
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file if it exists
this_directory = Path(__file__).parent
long_description = ""
readme_file = this_directory / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

setup(
    name="mokupdf",
    version="1.0.0",
    author="MokuPDF Team",
    author_email="mokupdf@example.com",
    description="MCP-compatible PDF reading server with intelligent file search and extraction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mokupdf/mokupdf",
    packages=find_packages(),
    keywords=["pdf", "mcp", "model-context-protocol", "ai", "llm", "claude", "pdf-reader", "text-extraction", "image-extraction"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyMuPDF>=1.23.0",
        "Pillow>=10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mokupdf=mokupdf.server:main",
        ],
    },
    package_data={
        "mokupdf": ["*.yaml", "*.json"],
    },
    include_package_data=True,
    zip_safe=False,
)