#!/usr/bin/env python3
"""
Verify what's actually saved in Supabase.
Shows the difference between raw OCR and Gemini analysis.
"""

import sys
import json
from gemini_supabase import check_cache

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_supabase.py <filename>")
        print("Example: python verify_supabase.py pg28-29.pdf")
        sys.exit(1)
    
    filename = sys.argv[1]
    print("=" * 60)
    print(f"🔍 Verifying Supabase data for: {filename}")
    print("=" * 60)
    print()
    
    result = check_cache(filename)
    if not result.get("cached"):
        print(f"❌ No cached data found for {filename}")
        return
    
    data = result["data"]
    
    # Check what columns exist
    print("📊 Columns in Supabase:")
    for key in sorted(data.keys()):
        if key not in ['id', 'created_at']:
            print(f"   ✅ {key}")
    print()
    
    # Show formatted_json (Gemini output)
    if 'formatted_json' in data:
        print("=" * 60)
        print("🤖 GEMINI ANALYSIS OUTPUT (formatted_json):")
        print("=" * 60)
        try:
            formatted = json.loads(data['formatted_json'])
            print(f"   Document Type: {formatted.get('document_type', 'N/A')}")
            print(f"   Total Pages: {formatted.get('total_pages', 'N/A')}")
            print(f"   Overall Summary: {formatted.get('overall_summary', 'N/A')[:200]}...")
            print(f"   Overall Keywords: {', '.join(formatted.get('overall_keywords', [])[:10])}")
            print()
            print("   Pages analyzed:")
            for page in formatted.get('pages', [])[:2]:  # Show first 2 pages
                print(f"      Page {page.get('page_number')}: {page.get('content_summary', 'N/A')[:100]}...")
        except Exception as e:
            print(f"   ❌ Error parsing formatted_json: {e}")
    else:
        print("❌ No formatted_json found (Gemini analysis missing)")
    
    print()
    print("=" * 60)
    print("📄 RAW OCR DATA (original_ocr_data):")
    print("=" * 60)
    
    # Show original_ocr_data (raw OCR)
    if 'original_ocr_data' in data:
        try:
            raw = json.loads(data['original_ocr_data'])
            print(f"   Filename: {raw.get('filename', 'N/A')}")
            print(f"   Total Pages: {raw.get('total_pages', 'N/A')}")
            print(f"   First page text preview: {raw.get('results', [{}])[0].get('text', 'N/A')[:200]}...")
        except Exception as e:
            print(f"   ❌ Error parsing original_ocr_data: {e}")
    else:
        print("   (No original_ocr_data column)")
    
    print()
    print("=" * 60)
    print("💡 TIP: In Supabase Dashboard, look at the 'formatted_json' column")
    print("   to see Gemini's analysis, not 'original_ocr_data' (raw OCR)")
    print("=" * 60)

if __name__ == "__main__":
    main()


