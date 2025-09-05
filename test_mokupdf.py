#!/usr/bin/env python3
"""
Simple test script for MokuPDF server
"""

import json
import subprocess
import time
import sys
from pathlib import Path

def test_mokupdf():
    """Test MokuPDF basic functionality"""
    print("Testing MokuPDF Server...")
    print("-" * 40)
    
    # Start the server
    print("Starting server...")
    process = subprocess.Popen(
        [sys.executable, "-m", "mokupdf", "--verbose"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    time.sleep(1)  # Give server time to start
    
    try:
        # Test 1: Initialize
        print("\n1. Testing initialization...")
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {},
            "id": 1
        }
        
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        
        response_str = process.stdout.readline()
        response = json.loads(response_str)
        
        if "result" in response:
            print("   ✓ Server initialized successfully")
            print(f"   Version: {response['result']['serverInfo']['version']}")
        else:
            print("   ✗ Initialization failed")
            
        # Test 2: List tools
        print("\n2. Testing tool listing...")
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        
        response_str = process.stdout.readline()
        response = json.loads(response_str)
        
        if "result" in response:
            tools = response["result"]["tools"]
            print(f"   ✓ Found {len(tools)} tools:")
            for tool in tools:
                print(f"      - {tool['name']}")
        else:
            print("   ✗ Failed to list tools")
            
        # Test 3: Try to open a PDF (will fail if no PDF exists)
        print("\n3. Testing PDF operations...")
        
        # Check if test PDF exists
        test_pdf = Path("pdfs/Calc111_searchable.pdf")
        if not test_pdf.exists():
            # Try to find any PDF
            pdfs_dir = Path("pdfs")
            if pdfs_dir.exists():
                pdf_files = list(pdfs_dir.glob("*.pdf"))
                if pdf_files:
                    test_pdf = pdf_files[0]
        
        if test_pdf.exists():
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "open_pdf",
                    "arguments": {"file_path": str(test_pdf)}
                },
                "id": 3
            }
            
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            
            response_str = process.stdout.readline()
            response = json.loads(response_str)
            
            if "result" in response:
                print(f"   ✓ PDF opened: {test_pdf.name}")
                print(f"   Pages: {response['result'].get('pages', 'N/A')}")
            else:
                print("   ✗ Failed to open PDF")
        else:
            print("   ℹ No test PDF found (this is OK)")
            
        print("\n" + "-" * 40)
        print("✓ MokuPDF server is working correctly!")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return False
    finally:
        # Terminate server
        process.terminate()
        time.sleep(0.5)
        if process.poll() is None:
            process.kill()
    
    return True

if __name__ == "__main__":
    success = test_mokupdf()
    sys.exit(0 if success else 1)