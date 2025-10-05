from mcp.server.fastmcp import FastMCP
import requests
from typing import Optional, Dict, Any

mcp = FastMCP("FetchMetalPrice")

# Constants for better maintainability
METAL_CONFIG = {
    "gold": {"symbol": "🥇", "price_key": "xauPrice", "import_duty": 0.06},
    "silver": {"symbol": "🥈", "price_key": "xagPrice", "import_duty": 0.075}
}

GST_RATE = 0.03
GRAMS_PER_OUNCE = 31.1035
FALLBACK_EXCHANGE_RATE = 83.0

# Common headers for API requests
COMMON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

def get_usd_to_inr_rate() -> float:
    """Get current USD to INR exchange rate with error handling"""
    try:
        response = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD",
            headers=COMMON_HEADERS,
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("rates", {}).get("INR", FALLBACK_EXCHANGE_RATE)
    except (requests.RequestException, KeyError, TypeError):
        return FALLBACK_EXCHANGE_RATE

def fetch_metal_data(headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Fetch metal price data from API"""
    try:
        response = requests.get(
            "https://data-asg.goldprice.org/dbXRates/USD",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json().get("items", [])
        return data[0] if data else None
    except (requests.RequestException, KeyError, IndexError, TypeError):
        return None

def calculate_prices(base_price: float, gst_rate: float, import_duty_rate: float) -> Dict[str, float]:
    """Calculate all price variations with taxes"""
    return {
        'with_gst': base_price * (1 + gst_rate),
        'with_import_duty': base_price * (1 + import_duty_rate),
        'total': base_price * (1 + gst_rate + import_duty_rate),
        'gst_amount': base_price * gst_rate,
        'duty_amount': base_price * import_duty_rate
    }

@mcp.tool()
def fetch_metal_price(metal: str = "gold") -> str:
    """
    Fetches current precious metal prices (gold or silver) in USD and converts to Indian Rupees.
    Shows comprehensive pricing with GST, import duty, and per-gram calculations.
    
    Args:
        metal: Metal type - "gold" or "silver" (default: "gold")
        
    Returns:
        Formatted string with complete price breakdown
    """
    try:
        # Input validation with detailed error message
        metal = metal.lower().strip()
        if metal not in METAL_CONFIG:
            valid_metals = ", ".join(f'"{m}"' for m in METAL_CONFIG.keys())
            return (f"❌ Invalid metal type: '{metal}'\n"
                   f"Please choose from: {valid_metals}")
        
        # Get metal configuration
        config = METAL_CONFIG[metal]
        metal_symbol = config["symbol"]
        price_key = config["price_key"]
        import_duty_rate = config["import_duty"]
        
        # Prepare headers for metal price API
        metal_headers = {
            **COMMON_HEADERS,
            'Referer': 'https://goldprice.org/',
            'Origin': 'https://goldprice.org',
            'DNT': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }
        
        # Fetch data concurrently (conceptually - in practice Python is single-threaded)
        metal_data = fetch_metal_data(metal_headers)
        exchange_rate = get_usd_to_inr_rate()
        
        if not metal_data:
            return f"❌ Unable to fetch {metal} price data from API"
            
        current_price_usd = metal_data.get(price_key)
        if not current_price_usd:
            return f"❌ {metal.title()} price not found in API response"
        
        # Calculate base prices
        current_price_inr = current_price_usd * exchange_rate
        price_per_10g_usd = (current_price_usd / GRAMS_PER_OUNCE) * 10
        price_per_10g_inr = (current_price_inr / GRAMS_PER_OUNCE) * 10
        
        # Calculate all price variations
        ounce_prices = calculate_prices(current_price_inr, GST_RATE, import_duty_rate)
        gram_prices = calculate_prices(price_per_10g_inr, GST_RATE, import_duty_rate)
        
        # Format output
        total_tax_rate = (GST_RATE + import_duty_rate) * 100
        
        return (
            f"{metal_symbol} Current {metal.title()} Price:\n\n"
            f"� Conversion: 1 Ounce = {GRAMS_PER_OUNCE:.4f} grams\n\n"
            f"�📈 Per Ounce:\n"
            f"  USD: ${current_price_usd:.2f}\n"
            f"  INR (Base): ₹{current_price_inr:,.2f}\n"
            f"  INR + GST (3%): ₹{ounce_prices['with_gst']:,.2f} (GST: ₹{ounce_prices['gst_amount']:,.2f})\n"
            f"  INR + Import Duty ({import_duty_rate*100:.1f}%): ₹{ounce_prices['with_import_duty']:,.2f} (Duty: ₹{ounce_prices['duty_amount']:,.2f})\n"
            f"  Market Price (GST + Duty): ₹{ounce_prices['total']:,.2f}\n\n"
            f"⚖️ Per 10 Grams:\n"
            f"  USD: ${price_per_10g_usd:.2f}\n"
            f"  INR (Base): ₹{price_per_10g_inr:,.2f}\n"
            f"  INR + GST (3%): ₹{gram_prices['with_gst']:,.2f} (GST: ₹{gram_prices['gst_amount']:,.2f})\n"
            f"  INR + Import Duty ({import_duty_rate*100:.1f}%): ₹{gram_prices['with_import_duty']:,.2f} (Duty: ₹{gram_prices['duty_amount']:,.2f})\n"
            f"  Market Price (GST + Duty): ₹{gram_prices['total']:,.2f}\n\n"
            f"📊 Exchange Rate: 1 USD = ₹{exchange_rate:.2f}\n"
            f"💼 Tax Summary: GST 3% + Import Duty {import_duty_rate*100:.1f}% = Total {total_tax_rate:.1f}%"
        )
        
    except Exception as e:
        return f"❌ Error fetching {metal} price: {str(e)}"