import re

def sanitize_mpn(mpn_str):
    """
    Strips tape-and-reel, packaging, and non-essential ordering suffixes 
    without altering core electrical MPN parameters.
    """
    clean = str(mpn_str).strip()
    clean = re.sub(r'(-TR|-REEL|-7-F|-T|\/REEL|\/TR)$', '', clean, flags=re.IGNORECASE)
    return clean

def parse_resistor_value(code_str):
    """Parses standard resistor value codes (e.g., '10KL' -> '10k Ohm', '120R' -> '120 Ohm')."""
    code = code_str.upper()
    if 'K' in code:
        val = code.replace('K', '').replace('L', '')
        return f"{val}k Ohm"
    elif 'M' in code:
        val = code.replace('M', '').replace('L', '')
        return f"{val}M Ohm"
    elif 'R' in code:
        val = code.replace('R', '').replace('L', '')
        return f"{val} Ohm"
    return "N/A"

def parse_samsung_voltage(v_code):
    """Parses Samsung MLCC voltage rating character codes."""
    voltage_map = {
        'A': '10 V',
        'B': '50 V',
        'C': '16 V',
        'E': '25 V',
        'G': '6.3 V',
        'P': '100 V'
    }
    return voltage_map.get(v_code.upper(), "N/A")

def decode_passive_component(mpn_str):
    """
    Dynamically decodes standard passive MPNs directly from part-numbering logic.
    No hardcoded default prices, voltages, or current values.
    """
    mpn = sanitize_mpn(mpn_str).upper()

    # 1. Yageo RC-Series Resistors (e.g., RC0805FR-0710KL)
    match_yageo = re.match(r'^RC(\d{4})[A-Z]+-07([0-9A-Z]+)$', mpn)
    if match_yageo:
        size = match_yageo.group(1)        # e.g., '0805'
        val_code = match_yageo.group(2)    # e.g., '10KL' or '120RL'
        
        resistance_val = parse_resistor_value(val_code)
        
        return {
            "MPN": mpn_str,
            "Manufacturer": "Yageo",
            "Category": "Resistors",
            "Description": f"Thick Film Chip Resistor {size} ({resistance_val})",
            "Lifecycle_Status": "Active",
            "Package": size,
            "Max_Voltage_V": "N/A",  # Left N/A unless explicitly derived from datasheet
            "Max_Current_A": "N/A",  # Left N/A unless explicitly derived from datasheet
            "Price_USD": "N/A",       # Never invent prices
            "Source": "Algorithmic Decoder"
        }

    # 2. Samsung CL-Series MLCC Capacitors (e.g., CL21B104KBCNNNC)
    match_samsung = re.match(r'^CL(\d{2})[A-Z](\d{3})[A-Z]([A-Z])', mpn)
    if match_samsung:
        size_code = match_samsung.group(1) # '21' -> 0805
        v_code = match_samsung.group(3)    # 'B' -> 50V
        
        package_size = "0805" if size_code == "21" else ("0603" if size_code == "10" else "N/A")
        voltage = parse_samsung_voltage(v_code)

        return {
            "MPN": mpn_str,
            "Manufacturer": "Samsung Electro-Mechanics",
            "Category": "Capacitors",
            "Description": f"Multilayer Ceramic Capacitor (MLCC) {package_size}",
            "Lifecycle_Status": "Active",
            "Package": package_size,
            "Max_Voltage_V": voltage,
            "Max_Current_A": "N/A",
            "Price_USD": "N/A",
            "Source": "Algorithmic Decoder"
        }

    # Not a recognized algorithmic passive structure
    return None
