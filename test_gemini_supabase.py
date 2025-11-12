#!/usr/bin/env python3
"""
Standalone test script for Gemini formatting and Supabase integration.
Tests without running expensive OCR/Modal operations.

Usage:
    python test_gemini_supabase.py
    python test_gemini_supabase.py --sample-json sample_data.json
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client, Client
from datetime import datetime

# Load environment variables
load_dotenv()

def get_gemini_model():
    """Initialize Gemini model."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash-lite-001')

def get_supabase_client():
    """Initialize Supabase client with validation."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
    
    # Validate and clean URL
    supabase_url = supabase_url.strip()
    if supabase_url.endswith('/'):
        supabase_url = supabase_url[:-1]
    
    if not supabase_url.startswith('https://'):
        raise ValueError(
            f"Invalid SUPABASE_URL format: '{supabase_url}'. "
            "URL must start with 'https://' (e.g., 'https://your-project.supabase.co')"
        )
    
    if '.supabase.co' not in supabase_url:
        raise ValueError(
            f"Invalid SUPABASE_URL format: '{supabase_url}'. "
            "URL should be in format: 'https://your-project-id.supabase.co'"
        )
    
    supabase_key = supabase_key.strip()
    if not supabase_key:
        raise ValueError("SUPABASE_KEY cannot be empty")
    
    return create_client(supabase_url, supabase_key)

def format_with_gemini(ocr_json_data: dict) -> str:
    """
    Format OCR JSON output using Gemini.
    
    Args:
        ocr_json_data: Dictionary containing OCR results
        
    Returns:
        Formatted JSON string from Gemini
    """
    try:
        model = get_gemini_model()
        
        prompt = f"""Please format and structure the following OCR output into a clean, well-organized JSON format.
        
The OCR output contains text extracted from a PDF document. Please:
1. Clean up any formatting issues
2. Structure the data logically
3. Preserve all important information
4. Return a valid JSON object

OCR Data:
{json.dumps(ocr_json_data, indent=2)}

Please return only the formatted JSON, no additional text or markdown formatting."""

        print("🤖 Calling Gemini API...")
        response = model.generate_content(prompt)
        formatted_output = response.text.strip()
        
        # Try to parse and validate JSON
        try:
            json.loads(formatted_output)
        except json.JSONDecodeError:
            # If Gemini didn't return pure JSON, try to extract it
            if "```json" in formatted_output:
                formatted_output = formatted_output.split("```json")[1].split("```")[0].strip()
            elif "```" in formatted_output:
                formatted_output = formatted_output.split("```")[1].split("```")[0].strip()
            # Try parsing again
            json.loads(formatted_output)
        
        print("✅ Gemini formatting completed")
        return formatted_output
    except Exception as e:
        print(f"⚠️ Error formatting with Gemini: {e}")
        return json.dumps(ocr_json_data, indent=2)

def save_to_supabase(filename: str, formatted_json: str, original_ocr_data: dict):
    """
    Save formatted OCR output to Supabase.
    
    Args:
        filename: Original PDF filename
        formatted_json: Gemini-formatted JSON string
        original_ocr_data: Original OCR results dictionary
        
    Returns:
        dict with 'success' bool and 'data' or 'error' message
    """
    try:
        supabase = get_supabase_client()
        
        record = {
            "filename": filename,
            "formatted_json": formatted_json,
            "original_ocr_data": json.dumps(original_ocr_data),
            "created_at": datetime.utcnow().isoformat(),
            "total_pages": original_ocr_data.get("total_pages", 0)
        }
        
        print("💾 Saving to Supabase...")
        response = supabase.table("ocr_results").insert(record).execute()
        
        print(f"✅ Saved to Supabase successfully!")
        print(f"   Record ID: {response.data[0].get('id', 'N/A') if response.data else 'N/A'}")
        return {"success": True, "data": response.data}
    except ValueError as e:
        error_msg = f"Supabase configuration error: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
    except RuntimeError as e:
        error_msg = f"Supabase connection error: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error saving to Supabase: {error_msg}")
        if "Name or service not known" in error_msg or "[Errno -2]" in error_msg:
            error_msg += " (Check SUPABASE_URL format: should be 'https://your-project.supabase.co')"
        elif "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            error_msg += " (Table 'ocr_results' may not exist. Create it in Supabase.)"
        return {"success": False, "error": error_msg}

def create_sample_ocr_data():
    """Create sample OCR data for testing."""
    return {
        "filename": "test_document.pdf",
        "total_pages": 2,
        "results": [
            {
                "page": 1,
                "text": "# Sample Document\n\nThis is a test page with some content.\n\n- Item 1\n- Item 2\n- Item 3",
                "status": "success"
            },
            {
                "page": 2,
                "text": "# Page 2\n\nMore test content here.\n\nSome additional text for testing purposes.",
                "status": "success"
            }
        ]
    }

def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test Gemini and Supabase integration")
    parser.add_argument(
        "--sample-json",
        type=str,
        help="Path to JSON file with sample OCR data (optional)"
    )
    parser.add_argument(
        "--skip-gemini",
        action="store_true",
        help="Skip Gemini formatting test"
    )
    parser.add_argument(
        "--skip-supabase",
        action="store_true",
        help="Skip Supabase save test"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧪 Gemini & Supabase Integration Test")
    print("=" * 60)
    print()
    
    # Load sample data
    if args.sample_json:
        print(f"📄 Loading sample data from: {args.sample_json}")
        try:
            with open(args.sample_json, 'r', encoding='utf-8') as f:
                ocr_data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load JSON file: {e}")
            sys.exit(1)
    else:
        print("📄 Using default sample OCR data")
        ocr_data = create_sample_ocr_data()
    
    print(f"   Filename: {ocr_data['filename']}")
    print(f"   Total pages: {ocr_data['total_pages']}")
    print()
    
    # Test Gemini formatting
    formatted_json = None
    if not args.skip_gemini:
        print("=" * 60)
        print("TEST 1: Gemini Formatting")
        print("=" * 60)
        try:
            formatted_json = format_with_gemini(ocr_data)
            print(f"\n📊 Formatted JSON length: {len(formatted_json)} characters")
            print(f"📋 Preview (first 200 chars):\n{formatted_json[:200]}...")
            print()
        except Exception as e:
            print(f"❌ Gemini test failed: {e}")
            print("   Continuing with original JSON...")
            formatted_json = json.dumps(ocr_data, indent=2)
    else:
        print("⏭️  Skipping Gemini test")
        formatted_json = json.dumps(ocr_data, indent=2)
        print()
    
    # Test Supabase saving
    if not args.skip_supabase:
        print("=" * 60)
        print("TEST 2: Supabase Storage")
        print("=" * 60)
        result = save_to_supabase(
            ocr_data['filename'],
            formatted_json,
            ocr_data
        )
        
        if result.get("success"):
            print("\n✅ Supabase test passed!")
        else:
            print(f"\n❌ Supabase test failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    else:
        print("⏭️  Skipping Supabase test")
    
    print()
    print("=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()

