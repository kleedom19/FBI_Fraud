"""
Test script for DeepSeek-OCR Modal API
Tests the deployed endpoint with sample PDF files.
"""
import requests
import sys
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


def test_ocr_endpoint(base_url: str, pdf_path: str):
    """Test the OCR endpoint with a PDF file."""
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


def save_results(result: dict, output_path: str = "ocr_results.json"):
    """Save OCR results to a JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_path}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")


def main():
    """Main test function."""
    print("=" * 60)
    print("🚀 DeepSeek-OCR API Test Suite")
    print("=" * 60)
    
    # Configuration
    # Replace this with your actual Modal endpoint URL after deployment
    # Example: "https://your-workspace--deepseek-ocr-serve.modal.run"
    BASE_URL = "https://kleedom--deepseek-ocr-serve.modal.run"
    
    # Check if URL is configured
    if BASE_URL == "https://kleedom--deepseek-ocr-serve.modal.run":
        print("\n⚠️  WARNING: Please update BASE_URL with your Modal endpoint URL")
        print("   After deploying, run: modal deploy deploy_modal.py")
        print("   Then copy the URL and paste it into this script")
        
        # For local testing during development
        print("\n💡 For local testing, you can use: http://localhost:8000")
        user_input = input("\nEnter your Modal endpoint URL (or press Enter for localhost:8000): ").strip()
        
        if user_input:
            BASE_URL = user_input.rstrip('/')
        else:
            BASE_URL = "http://localhost:8000"
    
    # Test PDF file path
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        print("\n📁 No PDF file specified.")
        pdf_path = input("Enter path to PDF file to test: ").strip().strip('"\'')
        
        if not pdf_path:
            print("❌ No file specified. Exiting.")
            sys.exit(1)
    
    # Run tests
    print(f"\n🎯 Testing endpoint: {BASE_URL}")
    
    # Test 1: Health check
    if not test_health_check(BASE_URL):
        print("\n❌ Health check failed. Make sure your Modal app is deployed and running.")
        sys.exit(1)
    
    # Test 2: OCR endpoint
    result = test_ocr_endpoint(BASE_URL, pdf_path)
    
    if result:
        # Save results
        save_results(result)
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Tests failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

