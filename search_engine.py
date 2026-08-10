import requests
import re
from bs4 import BeautifulSoup

def search_web_fallback(mpn):
    """
    Scrapes component specs from web search snippets when APIs return empty.
    """
    clean_mpn = re.sub(r'[^a-zA-Z0-9]', '', mpn)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # Simple HTML search query targeting datasheet specs
        url = f"https://html.duckduckgo.com/html/?q={clean_mpn}+datasheet+package+voltage"
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            snippets = " ".join([snippet.text for snippet in soup.find_all('a', class_='result__snippet')])
            
            voltage_match = re.search(r'(\d+(?:\.\d+)?\s*V)', snippets, re.IGNORECASE)
            package_match = re.search(r'(SOIC-\d+|LQFP-\d+|SOT-\d+|TO-\d+|0805|0603|QFN-\d+)', snippets, re.IGNORECASE)
            
            return {
                "MPN": mpn,
                "Manufacturer": "Extracted via Search",
                "Category": "General Component",
                "Description": f"Automated web search result for {mpn}",
                "Lifecycle_Status": "Active",
                "Package": package_match.group(1) if package_match else "N/A",
                "Max_Voltage_V": voltage_match.group(1) if voltage_match else "N/A",
                "Max_Current_A": "N/A",
                "Price_USD": "N/A",
                "Source": "Web Search Fallback"
            }
    except Exception:
        pass

    return None
