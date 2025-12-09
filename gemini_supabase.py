"""
Shared module for Gemini analysis and Supabase storage.
Used by ocr_endpoint.py, analyze_ocr.py, and analyze_server.py
"""

import os
import json
import re
import time
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types as genai_types
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def get_gemini_model():
    """Initialize Gemini model."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    # Use gemini-1.5-pro or gemini-2.0-flash-exp for larger output capacity
    # gemini-2.0-flash-lite has limited output tokens
    try:
        return genai.GenerativeModel('gemini-2.0-flash-exp')
    except:
        # Fallback to flash-lite if exp not available
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

def extract_year_from_filename(filename):
    """Extract year from filename (e.g., '2019agedata.pdf' -> 2019)."""
    match = re.search(r'(\d{4})', filename)
    return int(match.group(1)) if match else None

def format_with_gemini(ocr_json_data: dict) -> str:
    """Analyze OCR output using Gemini with retry logic for 429 errors."""
    model = get_gemini_model()
    
    filename = ocr_json_data.get("filename", "")
    
    # For very large documents, truncate OCR data to avoid token limits
    # Only truncate if absolutely necessary (>150KB), and preserve ALL pages with data
    ocr_data_str = json.dumps(ocr_json_data, indent=2)
    if len(ocr_data_str) > 150000:  # ~150KB limit (increased to preserve more data)
        print(f"Warning: Very large document ({len(ocr_data_str)} chars). Attempting to process all pages...")
        # Only truncate as last resort - try to keep all pages with actual data
        results = ocr_json_data.get("results", [])
        # Filter out pages that are just image references with no table data
        filtered_results = []
        for result in results:
            text = result.get("text", "")
            # Keep pages with tables or substantial text content
            if "<table>" in text or len(text) > 200:
                filtered_results.append(result)
        
        if len(filtered_results) < len(results):
            print(f"Filtered out {len(results) - len(filtered_results)} pages with only image references")
            ocr_json_data = {**ocr_json_data, "results": filtered_results}
            ocr_json_data["total_pages"] = len(filtered_results)
        
        # If still too large, only then truncate, but keep more pages
        ocr_data_str = json.dumps(ocr_json_data, indent=2)
        if len(ocr_data_str) > 150000 and len(filtered_results) > 8:
            print(f"Still too large after filtering. Keeping all pages with data...")
            # Don't truncate - let Gemini handle it, but send all pages
    
    prompt = f"""Analyze the following OCR output from an FBI fraud report PDF and extract FRAUD-SPECIFIC metrics and financial data.

CRITICAL: The OCR output contains HTML TABLES (e.g., <table><tr><td>...</td></tr></table>). You MUST parse these HTML tables and extract ALL data from them.

FOCUS ON EXTRACTING (ALL DATA TYPES ARE EQUALLY IMPORTANT):
1. **Financial Losses**: Dollar amounts lost to fraud (extract exact numbers, not ranges) - parse from HTML table cells
2. **Fraud Categories**: Types of fraud (e.g., "Business Email Compromise", "Investment Fraud", "Romance Scams") - extract ALL categories from HTML tables, not just top 5
3. **Victim Statistics**: Counts of victims by category, age group, or fraud type - extract ALL counts from HTML table rows
4. **State Data**: Fraud incidents, losses, or victim counts by US state (if available) - extract ALL states from HTML tables
5. **Trend/Comparison Data**: Multi-year comparisons (e.g., 2024 vs 2023 vs 2022) - extract data for ALL years and ALL categories from HTML tables
6. **Structured Tables**: Extract ALL data from HTML tables with numerical data (losses, counts, percentages) - parse every <tr> row and <td> cell
7. **Year/Time Period**: Extract the year or time period this data represents (look for years in table headers or content)
8. **Key Metrics**: Total losses, total victims, average loss per victim, top fraud categories

HOW TO PARSE HTML TABLES:
- Each <table> contains data you need to extract
- Each <tr> (table row) represents one data record
- Each <td> (table cell) contains a value (category name, number, dollar amount, etc.)
- Parse ALL rows - do not skip any
- For multi-column tables, match headers to data columns
- Extract numbers from cells (remove $, commas, and convert to integers/floats)
- For tables with years as columns (2024, 2023, 2022), extract data for each year

For each page, extract COMPLETE data from HTML tables:
- Tables with fraud statistics (category, loss amount, victim count) - extract ALL rows from HTML, not just top 5
- Financial figures (dollar amounts, losses, totals) - parse from HTML table cells, extract ALL amounts
- Fraud type classifications - extract ALL categories from ALL HTML tables
- Victim demographics (age groups, counts) - extract ALL demographics from HTML tables
- State-by-state data (if HTML tables show state information) - extract ALL states from HTML table rows
- Trend/comparison data - if HTML tables show multiple years (e.g., 2024, 2023, 2022), extract data for ALL years and ALL categories
- Year/period information - extract all years mentioned in HTML table headers or content

IMPORTANT: 
- If the OCR output only shows an image reference (like "![](images/0.jpg)"), note this in the content_summary
- If you see HTML tables (<table> tags), you MUST parse them and extract the data - do not skip them
- The data is in HTML format - parse the HTML structure to extract the actual values

EXAMPLE: If you see HTML like this:
<table><tr><td>Crime Type</td><td>Count</td></tr><tr><td>Phishing/Spoofing</td><td>23,252</td></tr><tr><td>Tech Support</td><td>16,777</td></tr></table>

You should extract:
- Row 1: category="Phishing/Spoofing", victim_count=23252
- Row 2: category="Tech Support", victim_count=16777

Parse EVERY row in EVERY table - extract ALL the data!

OCR Data:
{json.dumps(ocr_json_data, indent=2)}

Return a JSON object with this structure:
{{
  "filename": "document.pdf",
  "total_pages": 2,
  "year": 2020,
  "document_type": "fraud report",
  "pages": [
    {{
      "page_number": 1,
      "content_summary": "brief summary focusing on fraud metrics",
      "fraud_metrics": {{
        "tables": [
          {{
            "title": "Fraud Category or Age Group",
            "headers": ["Category", "Victim Count", "Total Loss"],
            "rows": [
              {{"category": "Category Name", "victim_count": 12345, "total_loss": 123456789, "year": 2020}}
            ]
          }},
          {{
            "title": "State Data",
            "headers": ["State", "Incidents", "Loss", "Victims"],
            "rows": [
              {{"state": "California", "incidents": 1234, "loss": 123456789, "victim_count": 12345}}
            ]
          }}
        ],
        "total_loss": 1234567890,
        "total_victims": 123456,
        "top_categories": ["Category 1", "Category 2"]
      }},
      "financial_data": {{
        "losses_by_category": [
          {{"category": "Category Name", "amount": 123456789, "victim_count": 12345}}
        ],
        "losses_by_state": [
          {{"state": "California", "amount": 123456789, "victim_count": 12345, "incidents": 1234}}
        ],
        "total_loss": 1234567890
      }}
    }}
  ],
  "overall_metrics": {{
    "total_loss": 1234567890,
    "total_victims": 123456,
    "year": 2020,
    "top_fraud_categories": ["Category 1", "Category 2", "Category 3"],
    "losses_by_category": [
      {{"category": "Category Name", "amount": 123456789, "victim_count": 12345}}
    ],
    "losses_by_state": [
      {{"state": "California", "amount": 123456789, "victim_count": 12345, "incidents": 1234}}
    ]
  }},
  "overall_summary": "concise summary of key fraud statistics"
}}

CRITICAL INSTRUCTIONS - EXTRACT ALL DATA FROM HTML TABLES:
- DO NOT include "raw_text" field - omit it completely
- PARSE HTML TABLES: The OCR output contains HTML tables (<table><tr><td>...</td></tr></table>) - you MUST parse these and extract ALL data
- EXTRACT ALL TABLES: Extract complete data from ALL HTML tables on ALL pages - parse every <tr> row and <td> cell, do not skip or truncate any tables
- EXTRACT ALL METRICS: Extract losses by category, victim counts, state data, trend data (multi-year comparisons), and any other numerical metrics from HTML tables
- EQUAL PRIORITY: All data types are equally important - crime type tables, loss tables, state tables, trend comparisons, etc.
- For each page with HTML tables, extract:
  * ALL rows from ALL HTML tables (parse every <tr>, do not limit to top 5 or top 10)
  * ALL categories with their counts and losses (from HTML table cells)
  * ALL states with their incidents and losses (from HTML table rows)
  * ALL years in trend/comparison tables (from HTML table headers or columns)
- Extract actual numbers from HTML table cells. Parse dollar amounts as numbers (remove $ and commas).
- If OCR shows image references, just note it in content_summary.
- If you see HTML table structure, parse it - the data is there in the HTML, extract it!
- Return ONLY valid JSON, no markdown, no code blocks, no explanatory text.
- Ensure all JSON strings are properly escaped.
- Do not include trailing commas.
- IMPORTANT: Extract complete data from pages 2-7 (crime types, losses, trends, states) - parse ALL HTML tables, do not skip any pages or truncate any tables."""

    max_retries = 3
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Use response_format to force JSON output (if supported)
            try:
                # Try using GenerationConfig for JSON mode with increased output tokens
                generation_config = {
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                    "max_output_tokens": 32768,  # Allow large JSON responses (32K tokens)
                }
                response = model.generate_content(
                    prompt, 
                    generation_config=generation_config
                )
            except (TypeError, AttributeError, ValueError) as config_err:
                # Fallback if response_format not supported or model doesn't support it
                print(f"Note: JSON mode not available, using standard mode")
                # Try with max_output_tokens in standard mode
                try:
                    generation_config = {
                        "temperature": 0.1,
                        "max_output_tokens": 32768,
                    }
                    response = model.generate_content(prompt, generation_config=generation_config)
                except:
                    response = model.generate_content(prompt)
            formatted_output = response.text.strip()
            
            # Try multiple JSON extraction strategies
            json_str = None
            
            # Strategy 1: Try direct parsing
            try:
                parsed = json.loads(formatted_output)
                if "pages" in parsed:
                    return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                pass
            
            # Strategy 2: Extract from markdown code blocks
            if "```json" in formatted_output:
                parts = formatted_output.split("```json")
                if len(parts) > 1:
                    json_str = parts[1].split("```")[0].strip()
            elif "```" in formatted_output:
                parts = formatted_output.split("```")
                if len(parts) > 1:
                    json_str = parts[1].split("```")[0].strip()
            
            # Strategy 3: Find JSON object boundaries
            if not json_str:
                start_idx = formatted_output.find('{')
                end_idx = formatted_output.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = formatted_output[start_idx:end_idx+1]
            
            # Strategy 4: Try to fix common JSON issues and handle truncation
            if json_str:
                # Remove trailing commas before closing braces/brackets
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                # Fix unescaped newlines in strings
                json_str = re.sub(r'(?<!\\)\n', '\\n', json_str)
                # Fix unescaped tabs
                json_str = re.sub(r'(?<!\\)\t', '\\t', json_str)
                
                # Check if JSON appears truncated (missing closing braces)
                open_count = json_str.count('{')
                close_count = json_str.count('}')
                open_arrays = json_str.count('[') - json_str.count(']')
                
                if open_count > close_count or open_arrays > 0:
                    missing_braces = open_count - close_count
                    missing_brackets = open_arrays
                    print(f"Warning: JSON appears truncated (missing {missing_braces} braces, {missing_brackets} brackets). Attempting to repair...")
                    
                    # Smart repair: close structures in reverse order
                    # First, find where the truncation likely occurred (last complete structure)
                    # Then close arrays first, then objects
                    repair_str = ''
                    if missing_brackets > 0:
                        repair_str += ']' * missing_brackets
                    if missing_braces > 0:
                        repair_str += '}' * missing_braces
                    
                    json_str += repair_str
                    print(f"Added {len(repair_str)} closing characters to repair JSON")
                
                    try:
                        parsed = json.loads(json_str)
                        if "pages" in parsed:
                            print("Successfully parsed JSON (after fixing truncation)")
                            return json.dumps(parsed, indent=2)
                    except json.JSONDecodeError as e:
                        # If repair failed, try using jsonrepair if available
                        try:
                            import jsonrepair
                            repaired = jsonrepair.repair_json(json_str)
                            parsed = json.loads(repaired)
                            if "pages" in parsed:
                                print("Successfully repaired JSON using jsonrepair library")
                                return json.dumps(parsed, indent=2)
                        except (ImportError, Exception):
                            pass  # jsonrepair not available or failed
                        
                        # Try to extract what we can from partial JSON
                        if attempt == max_retries - 1:
                            print("Attempting to extract partial data from truncated JSON...")
                            try:
                                # Try to find complete page objects
                                import re as regex_module
                                # Find all complete page objects (those that are properly closed)
                                page_pattern = r'"page_number":\s*\d+[^}]*"raw_text":\s*"[^"]*"\s*\}'
                                pages_found = regex_module.findall(page_pattern, json_str)
                                
                                # Try a simpler approach: find the last complete structure
                                # Look for the last complete page
                                last_complete_page_idx = json_str.rfind('"page_number"')
                                if last_complete_page_idx != -1:
                                    # Find where this page ends
                                    page_start = json_str.rfind('{', 0, last_complete_page_idx)
                                    # Try to find a matching closing brace
                                    brace_count = 0
                                    page_end = -1
                                    for i in range(page_start, len(json_str)):
                                        if json_str[i] == '{':
                                            brace_count += 1
                                        elif json_str[i] == '}':
                                            brace_count -= 1
                                            if brace_count == 0:
                                                page_end = i + 1
                                                break
                                    
                                    if page_end > page_start:
                                        # Extract everything up to and including the last complete page
                                        partial_json = json_str[:page_end]
                                        # Close the pages array and overall structure
                                        partial_json += '], "overall_metrics": {"total_loss": null, "total_victims": null, "year": ' + str(extract_year_from_filename(ocr_json_data.get("filename", ""))) + ', "top_fraud_categories": [], "losses_by_category": [], "losses_by_state": []}, "overall_summary": "Partial extraction due to response truncation"}'
                                        
                                        try:
                                            parsed = json.loads(partial_json)
                                            if "pages" in parsed:
                                                print(f"Successfully extracted {len(parsed.get('pages', []))} complete pages from truncated response")
                                                return json.dumps(parsed, indent=2)
                                        except:
                                            pass
                            except Exception as extract_err:
                                print(f"Could not extract partial data: {extract_err}")
                            
                            # Save error for debugging
                            try:
                                print(f"JSON parsing error at line {e.lineno}, col {e.colno}: {e.msg}")
                            except:
                                print(f"JSON parsing error: {str(e)}")
                            print(f"First 500 chars of response: {formatted_output[:500]}")
                            print(f"Last 500 chars of response: {formatted_output[-500:]}")
                            # Try to extract what we can
                            try:
                                # Find the error position and try to fix it
                                error_pos = e.pos if hasattr(e, 'pos') else None
                                if error_pos:
                                    print(f"Error at position {error_pos} in JSON string")
                                    # Try to fix common issues around error position
                                    if error_pos and error_pos < len(json_str):
                                        # Try removing problematic characters around error
                                        fixed_json = json_str[:error_pos] + json_str[error_pos+1:]
                                        try:
                                            parsed = json.loads(fixed_json)
                                            if "pages" in parsed:
                                                print("Fixed JSON by removing problematic character")
                                                return json.dumps(parsed, indent=2)
                                        except:
                                            pass
                            except Exception as fix_err:
                                print(f"Could not fix JSON error: {fix_err}")
            
            # If all strategies failed, continue to next attempt or fallback
            if attempt < max_retries - 1:
                continue
            else:
                # Last attempt failed - break to fallback
                break
                
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
                print(f"Gemini rate limit (429) - retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(delay)
                continue
            else:
                if is_rate_limit:
                    print(f"Gemini rate limit error after {max_retries} attempts: {e}")
                    if attempt == max_retries - 1:
                        break  # Go to fallback
                else:
                    print(f"Error analyzing with Gemini: {e}")
                    if attempt == max_retries - 1:
                        break  # Go to fallback instead of raising
                    else:
                        continue  # Try next attempt
    
    # If we get here, all retries failed - try extracting state data directly from HTML
    print("Gemini analysis failed after all retries - attempting direct HTML extraction for state data")
    state_data = []
    try:
        from extract_state_from_html import extract_state_data_from_html
        state_data = extract_state_data_from_html(ocr_json_data)
        print(f"Extracted {len(state_data)} state records directly from HTML tables")
    except Exception as e:
        print(f"Could not extract state data directly: {e}")
    
    # Build fallback structure
    fallback = {
        "filename": ocr_json_data.get("filename", "unknown"),
        "total_pages": ocr_json_data.get("total_pages", 0),
        "year": extract_year_from_filename(ocr_json_data.get("filename", "")),
        "document_type": "fraud report",
        "pages": [
            {
                "page_number": result.get("page", i+1),
                "content_summary": "Analysis failed - see raw_text",
                "fraud_metrics": {
                    "tables": [],
                    "total_loss": None,
                    "total_victims": None,
                    "top_categories": []
                },
                "financial_data": {
                    "losses_by_category": [],
                    "total_loss": None
                },
                "raw_text": ""  # Omitted to save tokens
            }
            for i, result in enumerate(ocr_json_data.get("results", []))
        ],
        "overall_metrics": {
            "total_loss": None,
            "total_victims": None,
            "year": extract_year_from_filename(ocr_json_data.get("filename", "")),
            "top_fraud_categories": [],
            "losses_by_category": [],
            "losses_by_state": [
                {
                    "state": item.get("state"),
                    "amount": item.get("loss"),
                    "victim_count": item.get("count"),
                    "incidents": item.get("incidents")
                }
                for item in state_data
            ] if state_data else []
        },
        "overall_summary": f"Gemini analysis failed - extracted {len(state_data)} state records from HTML" if state_data else "Gemini analysis failed - using raw OCR data"
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
                "raw_text_length": len(page.get("raw_text", "")),
            }
            
            # Extract fraud metrics if available
            fraud_metrics = page.get("fraud_metrics", {})
            if fraud_metrics:
                page_row["total_loss"] = fraud_metrics.get("total_loss")
                page_row["total_victims"] = fraud_metrics.get("total_victims")
                page_row["has_fraud_tables"] = len(fraud_metrics.get("tables", [])) > 0
                page_row["top_categories"] = ", ".join(fraud_metrics.get("top_categories", []))
            
            # Extract financial data if available
            financial_data = page.get("financial_data", {})
            if financial_data:
                page_row["financial_total_loss"] = financial_data.get("total_loss")
                page_row["num_categories"] = len(financial_data.get("losses_by_category", []))
            
            pages_data.append(page_row)
        
        df = pd.DataFrame(pages_data)
        
        # Extract overall metrics
        overall_metrics = gemini_analysis.get("overall_metrics", {})
        top_categories = overall_metrics.get("top_fraud_categories", []) if overall_metrics else []
        
        return {
            "dataframe": df.to_dict(orient="records"),
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": list(df.columns),
            "overall_keywords": top_categories,  # Use fraud categories as keywords
            "overall_summary": gemini_analysis.get("overall_summary", ""),
            "document_type": gemini_analysis.get("document_type", ""),
            "total_loss": overall_metrics.get("total_loss") if overall_metrics else None,
            "total_victims": overall_metrics.get("total_victims") if overall_metrics else None
        }
    except ImportError:
        return {
            "dataframe": [],
            "error": "pandas not available",
            "overall_keywords": [],
            "overall_summary": gemini_analysis.get("overall_summary", "")
        }
    except Exception as e:
        return {
            "dataframe": [],
            "error": str(e),
            "overall_keywords": [],
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
                overall_metrics = analysis_dict.get("overall_metrics", {})
                key_metrics = {
                    "document_type": analysis_dict.get("document_type", ""),
                    "overall_summary": analysis_dict.get("overall_summary", ""),
                    "total_pages_analyzed": len(analysis_dict.get("pages", [])),
                    "year": analysis_dict.get("year"),
                    "total_loss": overall_metrics.get("total_loss") if overall_metrics else None,
                    "total_victims": overall_metrics.get("total_victims") if overall_metrics else None,
                    "top_fraud_categories": overall_metrics.get("top_fraud_categories", []) if overall_metrics else []
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

