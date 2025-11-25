"""
Test script for DeepSeek-OCR Modal API
Tests the OCR endpoint only (Gemini/Supabase are separate).

Usage:
    python test_api.py path/to/file.pdf
    python test_api.py path/to/file.pdf --save-json  # Save OCR results for later analysis
"""
import requests
import sys
import argparse
from pathlib import Path
import json
import time


def test_health_check(base_url: str):
    """Test the health check endpoint."""
    print("\n🔍 Testing health check endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        response.raise_for_status()
        print(f"✅ Health check passed: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_ocr_endpoint(base_url: str, pdf_path: str, save_json: bool = False):
    """Test the OCR endpoint with a PDF file (OCR only, no Gemini/Supabase)."""
    print(f"\n📄 Testing OCR endpoint with: {pdf_path}")
    
    # Check if file exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ File not found: {pdf_path}")
        return None
    
    # Prepare the file for upload
    try:
        with open(pdf_file, 'rb') as f:
            files = {'file': (pdf_file.name, f, 'application/pdf')}
            
            print(f"📤 Uploading {pdf_file.name} ({pdf_file.stat().st_size / 1024:.2f} KB)...")
            print("⚠️  Note: This runs OCR only. Use analyze_ocr.py for Gemini analysis.")
            start_time = time.time()
            
            response = requests.post(
                f"{base_url}/ocr/pdf",
                files=files,
                timeout=300  # 5 minute timeout
            )
            
            elapsed_time = time.time() - start_time
            print(f"⏱️  Request completed in {elapsed_time:.2f} seconds")
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ OCR completed successfully!")
            print(f"📊 Results summary:")
            print(f"   - Filename: {result['filename']}")
            print(f"   - Total pages: {result['total_pages']}")
            print(f"\n💡 Next step: Run 'python analyze_ocr.py {pdf_file.stem}_ocr.json' to analyze with Gemini")
            
            # Display results for each page
            for page_result in result['results']:
                page_num = page_result['page']
                status = page_result['status']
                
                if status == 'success':
                    text = page_result['text']
                    print(f"\n📄 Page {page_num} - SUCCESS:")
                    print(f"   Text length: {len(text)} characters")
                    print(f"   Preview: {text[:200]}..." if len(text) > 200 else f"   Text: {text}")
                else:
                    error = page_result.get('error', 'Unknown error')
                    print(f"\n❌ Page {page_num} - FAILED: {error}")
            
            return result
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The PDF might be too large or the server is busy.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Server response: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def save_results(result: dict, output_path: str = None):
    """Save OCR results to a JSON file."""
    if output_path is None:
        filename = result.get('filename', 'ocr_output')
        if filename.endswith('.pdf'):
            filename = filename[:-4]
        output_path = f"{filename}_ocr.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
        return None


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test Modal OCR endpoint")
    parser.add_argument("pdf_file", help="Path to PDF file")
    parser.add_argument("--base-url", type=str, 
                       default="https://kleedom--deepseek-ocr-serve.modal.run",
                       help="Modal endpoint URL")
    parser.add_argument("--save-json", action="store_true",
                       help="Save OCR results to JSON file")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 DeepSeek-OCR API Test (OCR Only)")
    print("=" * 60)
    print("\n⚠️  Note: This tests OCR only. Gemini/Supabase are separate.")
    print("   Use 'python analyze_ocr.py <ocr_json>' or 'python client_pipeline.py <pdf>' for full pipeline")
    print()
    
    BASE_URL = args.base_url.rstrip('/')
    pdf_path = args.pdf_file
    
    # Run tests
    print(f"🎯 Testing endpoint: {BASE_URL}")
    
    # Test 1: Health check
    if not test_health_check(BASE_URL):
        print("\n❌ Health check failed. Make sure your Modal app is deployed and running.")
        sys.exit(1)
    
    # Test 2: OCR endpoint
    result = test_ocr_endpoint(BASE_URL, pdf_path, save_json=args.save_json)
    
    if result:
        # Save results
        output_file = save_results(result)
        
        print("\n" + "=" * 60)
        print("✅ OCR test completed successfully!")
        print(f"📄 OCR results saved to: {output_file}")
        print(f"\n💡 Next steps:")
        print(f"   1. Analyze with Gemini: python analyze_ocr.py {output_file}")
        print(f"   2. Or run full pipeline: python client_pipeline.py {pdf_path}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ OCR test failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

