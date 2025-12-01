"""Extract state data directly from HTML tables in OCR output."""

import re
import json

def extract_state_data_from_html(ocr_json_data):
    """Extract state data directly from HTML tables."""
    # Use dict to merge counts and losses by state
    state_dict = {}
    results = ocr_json_data.get("results", [])
    
    for result in results:
        text = result.get("text", "")
        page = result.get("page", 0)
        
        # Look for state tables - they have "State" in headers and state names
        # Check for both count tables and loss tables
        is_state_table = "State" in text and ("Rank" in text or "Count" in text or "Loss" in text or "LOSSES BY STATE" in text.upper())
        
        if is_state_table:
            # Extract ALL tables from this page
            tables = re.findall(r'<table>(.*?)</table>', text, re.DOTALL)
            for table_html in tables:
                rows = re.findall(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
                
                # Check if this is a loss table (has $ or "Loss" in header)
                has_dollar = '$' in table_html or '&#36;' in table_html or "LOSS" in text.upper()
                
                # US state names for validation
                us_states = [
                    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
                    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
                    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
                    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
                    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
                    "New Hampshire", "New Jersey", "New Mexico", "New York",
                    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
                    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
                    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
                    "West Virginia", "Wisconsin", "Wyoming", "District of Columbia"
                ]
                
                for row in rows:
                    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                    if len(cells) >= 2:
                        # Clean cell content
                        cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]
                        cells = [re.sub(r'&#36;', '$', cell) for cell in cells]  # Fix $ encoding
                        
                        # Look for state name
                        state = None
                        for cell in cells:
                            # Check if cell contains a state name
                            for us_state in us_states:
                                if us_state.lower() in cell.lower():
                                    state = us_state
                                    break
                            if state:
                                break
                        
                        # Handle "District of" -> "District of Columbia"
                        if not state:
                            for cell in cells:
                                if "district of" in cell.lower() and "columbia" not in cell.lower():
                                    state = "District of Columbia"
                                    break
                        
                        if state:
                            # Extract numbers
                            for i, cell in enumerate(cells):
                                # Skip the state name cell and rank
                                if state.lower() in cell.lower() or cell.strip().isdigit():
                                    continue
                                
                                # Remove $, &#36; (HTML encoded $), and commas, try to parse as number
                                clean_cell = cell.replace('$', '').replace('&#36;', '').replace(',', '').strip()
                                try:
                                    num = int(float(clean_cell)) if '.' in clean_cell else int(clean_cell)
                                    if num > 100:  # Reasonable threshold
                                        # Initialize state entry if not exists
                                        if state not in state_dict:
                                            state_dict[state] = {"state": state, "loss": None, "count": None, "incidents": None}
                                        
                                        if has_dollar:
                                            # This is a loss amount
                                            if state_dict[state]["loss"] is None or num > state_dict[state]["loss"]:
                                                state_dict[state]["loss"] = num
                                        else:
                                            # This is a count
                                            if state_dict[state]["count"] is None or num > state_dict[state]["count"]:
                                                state_dict[state]["count"] = num
                                                state_dict[state]["incidents"] = num
                                except:
                                    pass
    
    # Convert dict to list
    return list(state_dict.values())

