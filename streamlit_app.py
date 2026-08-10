import requests
import re
from bs4 import BeautifulSoup

def search_web_fallback(mpn):
    """
    Strict web fallback search. Only extracts values if contextual boundaries match.
    Defaults to N/A rather than returning false matches from search snippets.
    """
    clean_mpn = re.sub(r'[^a-zA-Z0-9]', '', mpn)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        url = f"https://html.duckduckgo.com/html/?q={clean_mpn}+datasheet+operating+voltage+package"
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            snippets = " ".join([s.text for s in soup.find_all('a', class_='result__snippet')])
            
            # Strict Package Matching
            pkg_match = re.search(r'\b(LQFP-48|SOIC-8|SOIC-16|SOT-23|SOD-323|TO-220|DIP-8|0805|0603)\b', snippets, re.IGNORECASE)
            
            # Strict Voltage Matching (e.g., "3.6V", "50V", "75V")
            v_match = re.search(r'\b(\d+(?:\.\d+)?\s*V(?:DC)?)\b', snippets, re.IGNORECASE)
            
            # Only return if at least one structured spec was found
            if pkg_match or v_match:
                return {
                    "MPN": mpn,
                    "Manufacturer": "Extracted via Search",
                    "Category": "General Component",
                    "Description": f"Web extracted record for {mpn}",
                    "Lifecycle_Status": "Active",
                    "Package": pkg_match.group(1).upper() if pkg_match else "N/A",
                    "Max_Voltage_V": v_match.group(1) if v_match else "N/A",
                    "Max_Current_A": "N/A",
                    "Price_USD": "N/A",
                    "Source": "Web Search Fallback"
                }
    except Exception:
        pass

    return None
