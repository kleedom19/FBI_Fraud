#!/usr/bin/env python3
"""
Standalone script to analyze OCR output with Gemini and save to Supabase.
Works completely independently of Modal - no Modal required!

Usage:
    python analyze_ocr.py ocr_results.json
    python analyze_ocr.py --from-supabase filename.pdf  # Analyze from cached OCR
    python analyze_ocr.py --check-cache filename.pdf   # Just check if cached
"""

import os
import sys
import json
import argparse
from pathlib import Path
from gemini_supabase import (
    format_with_gemini,
    convert_to_dataframe,
    save_to_supabase,
    check_cache,
    get_ocr_from_supabase,
    delete_cache,
    delete_all_cache
)

def main():
    parser = argparse.ArgumentParser(description="Analyze OCR output with Gemini and save to Supabase")
    parser.add_argument("input_file", nargs="?", help="Path to OCR JSON file")
    parser.add_argument("--from-supabase", type=str, help="Analyze OCR data cached in Supabase for this filename")
    parser.add_argument("--check-cache", type=str, help="Check if analysis exists in cache for this filename")
    parser.add_argument("--delete-cache", type=str, help="Delete cached analysis for this filename")
    parser.add_argument("--delete-all-cache", action="store_true", help="Delete ALL cached analyses (use with caution!)")
    parser.add_argument("--skip-gemini", action="store_true", help="Skip Gemini analysis (use cached)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("OCR Analysis Pipeline (Standalone - No Modal Required)")
    print("=" * 60)
    print()
    
    # Delete all cache mode
    if args.delete_all_cache:
        print("WARNING: This will delete ALL cached analyses!")
        confirm = input("Type 'DELETE ALL' to confirm: ")
        if confirm == "DELETE ALL":
            print("Deleting all cached analyses...")
            result = delete_all_cache()
            if result.get("success"):
                count = result.get("deleted_count", 0)
                print(f"Deleted {count} cached entries")
            else:
                print(f"Failed to delete cache: {result.get('error')}")
        else:
            print("Cancelled - cache not deleted")
        return
    
    # Delete cache mode
    if args.delete_cache:
        print(f"Deleting cache for: {args.delete_cache}")
        result = delete_cache(args.delete_cache)
        if result.get("success"):
            count = result.get("deleted_count", 0)
            print(f"Deleted {count} cached entry/entries for {args.delete_cache}")
        else:
            print(f"Failed to delete cache: {result.get('error')}")
        return
    
    # Check cache mode
    if args.check_cache:
        print(f"Checking cache for: {args.check_cache}")
        result = check_cache(args.check_cache)
        if result.get("cached"):
            print(f"Found cached analysis!")
            cached_data = result['data']
            # Try to get document type from key_metrics
            key_metrics = cached_data.get('key_metrics')
            if key_metrics:
                if isinstance(key_metrics, str):
                    key_metrics = json.loads(key_metrics)
                doc_type = key_metrics.get('document_type', 'N/A')
            else:
                doc_type = 'N/A'
            print(f"   Document type: {doc_type}")
            print(f"   Cached at: {cached_data.get('cached_at', 'N/A')}")
            return
        else:
            print(f"No cached data found for {args.check_cache}")
            return
    
    # Load OCR data
    ocr_data = None
    
    if args.from_supabase:
        print(f"Loading OCR data from Supabase cache for: {args.from_supabase}")
        ocr_data = get_ocr_from_supabase(args.from_supabase)
        if not ocr_data:
            print(f"No OCR data found in cache for {args.from_supabase}")
            print("   Run OCR first or provide OCR JSON file")
            sys.exit(1)
    elif args.input_file:
        print(f"Loading OCR data from: {args.input_file}")
        with open(args.input_file, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)
    else:
        print("No input provided. Use --help for usage")
        sys.exit(1)
    
    filename = ocr_data.get("filename", "unknown.pdf")
    print(f"   Filename: {filename}")
    print(f"   Total pages: {ocr_data.get('total_pages', 0)}")
    print()
    
    # Check cache first
    print(f"Checking cache for {filename}...")
    cache_result = check_cache(filename)
    if cache_result.get("cached") and not args.skip_gemini:
        print("Found cached analysis! Use --skip-gemini to skip re-analysis")
        print(f"   Cached at: {cache_result['data'].get('cached_at', 'N/A')}")
        return
    
    # Analyze with Gemini
    if not args.skip_gemini:
        print("Analyzing with Gemini...")
        try:
            formatted_json = format_with_gemini(ocr_data)
            gemini_analysis = json.loads(formatted_json)
            
            # Check if Gemini actually analyzed or used fallback
            if gemini_analysis.get("overall_summary") == "Gemini analysis failed - using raw OCR data":
                print("WARNING: Gemini analysis failed - using fallback structure")
                print("   This means Gemini didn't process the data. Check your GEMINI_API_KEY.")
            else:
                print(f"Gemini analysis successful!")
                print(f"   Document type: {gemini_analysis.get('document_type', 'N/A')}")
                print(f"   Summary: {gemini_analysis.get('overall_summary', 'N/A')[:80]}...")
            
            # Convert to DataFrame
            print("Converting to DataFrame...")
            dataframe_data = convert_to_dataframe(gemini_analysis)
            print(f"   DataFrame shape: {dataframe_data['shape']}")
            
            # Save to Supabase
            print("Saving to Supabase...")
            result = save_to_supabase(filename, formatted_json, ocr_data, dataframe_data)
            
            if result.get("success"):
                print("\nAnalysis complete and saved to Supabase!")
                print(f"   Keywords: {', '.join(dataframe_data.get('overall_keywords', [])[:5])}...")
                print(f"\nTo verify: Check Supabase table 'ocr_results', column 'formatted_json'")
            else:
                print(f"\nAnalysis complete but Supabase save failed: {result.get('error')}")
        except Exception as e:
            print(f"\nError during Gemini analysis: {e}")
            print("   Check your GEMINI_API_KEY in .env file")
            import traceback
            traceback.print_exc()
    else:
        print("Skipping Gemini analysis (using --skip-gemini)")

if __name__ == "__main__":
    main()
