#!/usr/bin/env python3
"""
Client script that orchestrates the complete pipeline:
1. Check Supabase cache (avoid expensive OCR if already done)
2. Run OCR on Modal (if not cached)
3. Analyze OCR with Gemini (standalone, no Modal)
4. Save to Supabase

Usage:
    python client_pipeline.py path/to/file.pdf
    python client_pipeline.py path/to/file.pdf --skip-ocr  # Use existing OCR JSON
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import shared Gemini/Supabase functions
from gemini_supabase import (
    check_cache,
    get_ocr_from_supabase,
    format_with_gemini,
    convert_to_dataframe,
    save_to_supabase
)

def run_ocr_on_modal(pdf_path: str, modal_endpoint: str) -> dict:
    """
    Run OCR on Modal endpoint.
    
    Args:
        pdf_path: Path to PDF file
        modal_endpoint: Modal endpoint URL
        
    Returns:
        OCR results dictionary
    """
    print(f"📤 Uploading {pdf_path} to Modal OCR endpoint...")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
        response = requests.post(
            f"{modal_endpoint}/ocr/pdf",
            files=files,
            timeout=600  # 10 minute timeout for OCR
        )
        response.raise_for_status()
        return response.json()

def main():
    parser = argparse.ArgumentParser(description="Complete OCR → Gemini → Supabase pipeline")
    parser.add_argument("pdf_file", help="Path to PDF file to process")
    parser.add_argument("--modal-endpoint", type=str, 
                       default="https://kleedom--deepseek-ocr-serve.modal.run",
                       help="Modal OCR endpoint URL")
    parser.add_argument("--ocr-json", type=str, help="Use existing OCR JSON file instead of running OCR")
    parser.add_argument("--skip-ocr", action="store_true", help="Skip OCR, analyze existing data from Supabase")
    parser.add_argument("--skip-analysis", action="store_true", help="Only run OCR, skip Gemini analysis")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Complete OCR Pipeline (Modal → Gemini → Supabase)")
    print("=" * 60)
    print()
    
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)
    
    filename = pdf_path.name
    
    # Step 1: Check cache
    print("=" * 60)
    print("STEP 1: Checking Supabase Cache")
    print("=" * 60)
    cache_result = check_cache(filename)
    
    if cache_result.get("cached"):
        print(f"✅ Found cached analysis for {filename}!")
        cached_data = cache_result["data"]
        
        # Safely extract document type from key_metrics
        key_metrics = cached_data.get('key_metrics')
        if key_metrics:
            if isinstance(key_metrics, str):
                try:
                    key_metrics = json.loads(key_metrics)
                except:
                    key_metrics = {}
        else:
            key_metrics = {}
        
        doc_type = key_metrics.get('document_type', 'N/A') if key_metrics else 'N/A'
        print(f"   Document type: {doc_type}")
        print(f"   Cached at: {cached_data.get('cached_at', 'N/A')}")
        
        if not args.skip_analysis:
            print("\n💡 To re-analyze, delete from Supabase or use --skip-ocr with new OCR data")
        return
    
    print(f"❌ No cached data found for {filename}")
    print()
    
    # Step 2: Run OCR (if needed)
    ocr_data = None
    
    if args.ocr_json:
        print("=" * 60)
        print("STEP 2: Loading OCR from JSON File")
        print("=" * 60)
        print(f"📄 Loading from: {args.ocr_json}")
        with open(args.ocr_json, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)
    elif args.skip_ocr:
        print("=" * 60)
        print("STEP 2: Loading OCR from Supabase Cache")
        print("=" * 60)
        ocr_data = get_ocr_from_supabase(filename)
        if not ocr_data:
            print(f"❌ No OCR data found in cache. Run OCR first.")
            sys.exit(1)
    else:
        print("=" * 60)
        print("STEP 2: Running OCR on Modal (This costs money!)")
        print("=" * 60)
        try:
            ocr_data = run_ocr_on_modal(str(pdf_path), args.modal_endpoint)
            print(f"✅ OCR completed: {ocr_data.get('total_pages', 0)} pages")
            
            # Optionally save OCR results to file
            ocr_output_file = f"{pdf_path.stem}_ocr.json"
            with open(ocr_output_file, 'w', encoding='utf-8') as f:
                json.dump(ocr_data, f, indent=2)
            print(f"💾 OCR results saved to: {ocr_output_file}")
        except Exception as e:
            print(f"❌ OCR failed: {e}")
            sys.exit(1)
    
    print()
    
    # Step 3: Analyze with Gemini (if not skipping)
    if args.skip_analysis:
        print("⏭️  Skipping Gemini analysis (--skip-analysis)")
        return
    
    print("=" * 60)
    print("STEP 3: Analyzing with Gemini (Standalone - No Modal)")
    print("=" * 60)
    
    try:
        # Analyze with Gemini
        formatted_json = format_with_gemini(ocr_data)
        gemini_analysis = json.loads(formatted_json)
        
        # Convert to DataFrame
        print("📊 Converting to DataFrame...")
        dataframe_data = convert_to_dataframe(gemini_analysis)
        print(f"   DataFrame shape: {dataframe_data['shape']}")
        
        # Step 4: Save to Supabase
        print()
        print("=" * 60)
        print("STEP 4: Saving to Supabase")
        print("=" * 60)
        
        result = save_to_supabase(filename, formatted_json, ocr_data, dataframe_data)
        
        if result.get("success"):
            print("\n✅ Pipeline complete!")
            print(f"   Filename: {filename}")
            print(f"   Document type: {dataframe_data.get('document_type', 'N/A')}")
            print(f"   Keywords: {', '.join(dataframe_data.get('overall_keywords', [])[:5])}...")
            print(f"   Saved to Supabase with DataFrame")
        else:
            print(f"\n⚠️ Analysis complete but Supabase save failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

