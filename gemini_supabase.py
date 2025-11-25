"""
Shared module for Gemini analysis and Supabase storage.
Used by ocr_endpoint.py, analyze_ocr.py, and analyze_server.py
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def get_gemini_model():
    """Initialize Gemini model."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash-lite')

def get_supabase_client():
    """Initialize Supabase client with validation."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
    
    supabase_url = supabase_url.strip()
    if supabase_url.endswith('/'):
        supabase_url = supabase_url[:-1]
    
    if not supabase_url.startswith('https://'):
        raise ValueError(f"Invalid SUPABASE_URL format: '{supabase_url}'. Must start with 'https://'")
    
    if '.supabase.co' not in supabase_url:
        raise ValueError(f"Invalid SUPABASE_URL format: '{supabase_url}'. Should be 'https://your-project.supabase.co'")
    
    supabase_key = supabase_key.strip()
    if not supabase_key:
        raise ValueError("SUPABASE_KEY cannot be empty")
    
    return create_client(supabase_url, supabase_key)

def format_with_gemini(ocr_json_data: dict) -> str:
    """Analyze OCR output using Gemini with retry logic for 429 errors."""
    model = get_gemini_model()
    
    prompt = f"""Analyze the following OCR output from a PDF document and extract structured insights.

For each page, please provide:
1. **Content Summary**: A brief summary of what the page contains
2. **Document Type**: What type of document this is (report, form, table, etc.)
3. **Key Information**: Important facts, numbers, dates, names, or data points
4. **Top Keywords**: 5-10 most important keywords/topics from the page
5. **Images/Visual Elements**: If any images, tables, or visual elements are mentioned, describe what information they contain
6. **Structured Data**: Extract any tables, lists, or structured data into a clean format
7. **Main Topics**: Main themes or subjects discussed

OCR Data:
{json.dumps(ocr_json_data, indent=2)}

Return a JSON object with this structure:
{{
  "filename": "document.pdf",
  "total_pages": 2,
  "document_type": "overall document type",
  "pages": [
    {{
      "page_number": 1,
      "content_summary": "brief summary of page content",
      "document_type": "type of content on this page",
      "key_information": ["important fact 1", "important fact 2", ...],
      "top_keywords": ["keyword1", "keyword2", ...],
      "images_visual_elements": ["description of image/table 1", ...],
      "structured_data": {{"tables": [...], "lists": [...]}},
      "main_topics": ["topic1", "topic2", ...],
      "raw_text": "original OCR text for reference"
    }}
  ],
  "overall_keywords": ["top keywords across all pages"],
  "overall_summary": "summary of entire document"
}}

Return ONLY valid JSON, no markdown formatting or additional text."""

    max_retries = 3
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            formatted_output = response.text.strip()
            
            try:
                parsed = json.loads(formatted_output)
                if "pages" not in parsed:
                    raise ValueError("Missing 'pages' key in Gemini response")
                return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                if "```json" in formatted_output:
                    formatted_output = formatted_output.split("```json")[1].split("```")[0].strip()
                elif "```" in formatted_output:
                    formatted_output = formatted_output.split("```")[1].split("```")[0].strip()
                parsed = json.loads(formatted_output)
                if "pages" not in parsed:
                    raise ValueError("Missing 'pages' key in Gemini response")
                return json.dumps(parsed, indent=2)
                
        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = (
                "429" in error_str or 
                "resource exhausted" in error_str or 
                "rate limit" in error_str or
                "quota" in error_str
            )
            
            if is_rate_limit and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"⚠️ Gemini rate limit (429) - retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(delay)
                continue
            else:
                if is_rate_limit:
                    print(f"⚠️ Gemini rate limit error after {max_retries} attempts: {e}")
                else:
                    print(f"⚠️ Error analyzing with Gemini: {e}")
                raise
    
    # If we get here, all retries failed - return fallback
    print("⚠️ Gemini analysis failed after all retries - using fallback structure")
    fallback = {
        "filename": ocr_json_data.get("filename", "unknown"),
        "total_pages": ocr_json_data.get("total_pages", 0),
        "document_type": "unknown",
        "pages": [
            {
                "page_number": result.get("page", i+1),
                "content_summary": "Analysis failed - see raw_text",
                "document_type": "unknown",
                "key_information": [],
                "top_keywords": [],
                "images_visual_elements": [],
                "structured_data": {},
                "main_topics": [],
                "raw_text": result.get("text", "")
            }
            for i, result in enumerate(ocr_json_data.get("results", []))
        ],
        "overall_keywords": [],
        "overall_summary": "Gemini analysis failed - using raw OCR data"
    }
    return json.dumps(fallback, indent=2)

def convert_to_dataframe(gemini_analysis: dict) -> dict:
    """Convert Gemini analysis output to a pandas DataFrame structure."""
    try:
        import pandas as pd
        
        pages_data = []
        for page in gemini_analysis.get("pages", []):
            page_row = {
                "page_number": page.get("page_number", 0),
                "filename": gemini_analysis.get("filename", "unknown"),
                "content_summary": page.get("content_summary", ""),
                "document_type": page.get("document_type", ""),
                "key_information": ", ".join(page.get("key_information", [])),
                "top_keywords": ", ".join(page.get("top_keywords", [])),
                "images_visual_elements": ", ".join(page.get("images_visual_elements", [])),
                "main_topics": ", ".join(page.get("main_topics", [])),
                "raw_text_length": len(page.get("raw_text", "")),
            }
            structured = page.get("structured_data", {})
            page_row["has_tables"] = len(structured.get("tables", [])) > 0 if structured else False
            page_row["has_lists"] = len(structured.get("lists", [])) > 0 if structured else False
            pages_data.append(page_row)
        
        df = pd.DataFrame(pages_data)
        
        return {
            "dataframe": df.to_dict(orient="records"),
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": list(df.columns),
            "overall_keywords": gemini_analysis.get("overall_keywords", []),
            "overall_summary": gemini_analysis.get("overall_summary", ""),
            "document_type": gemini_analysis.get("document_type", "")
        }
    except ImportError:
        return {
            "dataframe": [],
            "error": "pandas not available",
            "overall_keywords": gemini_analysis.get("overall_keywords", []),
            "overall_summary": gemini_analysis.get("overall_summary", "")
        }
    except Exception as e:
        return {
            "dataframe": [],
            "error": str(e),
            "overall_keywords": gemini_analysis.get("overall_keywords", []),
            "overall_summary": gemini_analysis.get("overall_summary", "")
        }

def save_to_supabase(filename: str, formatted_json: str, original_ocr_data: dict, dataframe_data: dict = None):
    """Save formatted OCR output to Supabase."""
    try:
        supabase = get_supabase_client()
        
        # Start with required columns only
        record = {
            "filename": filename,
            "formatted_json": formatted_json,
            "original_ocr_data": json.dumps(original_ocr_data),
            "created_at": datetime.utcnow().isoformat(),
            "total_pages": original_ocr_data.get("total_pages", 0)
        }
        
        # Add optional columns if dataframe_data is provided
        optional_fields = {}
        if dataframe_data:
            optional_fields["dataframe_json"] = json.dumps(dataframe_data.get("dataframe", []))
            optional_fields["keywords"] = dataframe_data.get("overall_keywords", [])
            try:
                analysis_dict = json.loads(formatted_json)
                key_metrics = {
                    "document_type": analysis_dict.get("document_type", ""),
                    "overall_summary": analysis_dict.get("overall_summary", ""),
                    "total_pages_analyzed": len(analysis_dict.get("pages", []))
                }
                optional_fields["key_metrics"] = json.dumps(key_metrics)
            except:
                pass
        
        # Try with all optional fields first
        full_record = {**record, **optional_fields}
        full_record["ocr_raw_data"] = json.dumps(original_ocr_data)
        full_record["cached_at"] = datetime.utcnow().isoformat()
        
        # Try inserting with all fields, then fallback to minimal if needed
        for attempt in [full_record, {**record, **optional_fields}, record]:
            try:
                response = supabase.table("ocr_results").insert(attempt).execute()
                return {"success": True, "data": response.data}
            except Exception as e:
                error_str = str(e).lower()
                # If it's a column error, try with fewer fields
                if "pgrst204" in error_str or "could not find" in error_str:
                    continue
                # For other errors, return immediately
                error_msg = str(e)
                if "row-level security" in error_msg.lower() or "42501" in error_msg:
                    error_msg += " (Hint: Use SUPABASE_SERVICE_KEY to bypass RLS)"
                return {"success": False, "error": error_msg}
        
        # If all attempts failed, return the last error
        return {"success": False, "error": "Failed to insert with any column combination"}
    except Exception as e:
        error_msg = str(e)
        if "row-level security" in error_msg.lower() or "42501" in error_msg:
            error_msg += " (Hint: Use SUPABASE_SERVICE_KEY to bypass RLS)"
        return {"success": False, "error": error_msg}

def check_cache(filename: str):
    """Check if analysis already exists in Supabase."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("ocr_results").select("*").eq("filename", filename).execute()
        
        if response.data and len(response.data) > 0:
            latest = sorted(response.data, key=lambda x: x.get("cached_at", ""), reverse=True)[0]
            return {"cached": True, "data": latest}
        return {"cached": False, "data": None}
    except Exception as e:
        return {"cached": False, "error": str(e)}

def get_ocr_from_supabase(filename: str):
    """Retrieve raw OCR data from Supabase cache."""
    cache_result = check_cache(filename)
    if cache_result.get("cached"):
        cached_data = cache_result["data"]
        if "ocr_raw_data" in cached_data:
            return json.loads(cached_data["ocr_raw_data"])
        elif "original_ocr_data" in cached_data:
            return json.loads(cached_data["original_ocr_data"])
    return None

def delete_cache(filename: str):
    """Delete cached analysis from Supabase."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("ocr_results").delete().eq("filename", filename).execute()
        deleted_count = len(response.data) if response.data else 0
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_all_cache():
    """Delete ALL cached analyses from Supabase. Use with caution!"""
    try:
        supabase = get_supabase_client()
        # Get count first
        count_response = supabase.table("ocr_results").select("id", count="exact").execute()
        total_count = count_response.count if hasattr(count_response, 'count') else 0
        
        # Delete all
        response = supabase.table("ocr_results").delete().neq("id", 0).execute()  # neq("id", 0) matches all rows
        deleted_count = len(response.data) if response.data else total_count
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        return {"success": False, "error": str(e)}

