import os
import time
import telebot
import schedule
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from groq import Groq

# =====================================================================
# 1. KONFIGURASI & API KEYS
# =====================================================================
# Token Telegram kau
TELEGRAM_BOT_TOKEN = "8673710597:AAGD4I53588YSL1QK9ZllzlaeQY68gFttSQ"
# Tarik API Key Groq dari Render Environment Variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
VIP_CHANNEL_ID = "-1003943365561"
ADMIN_ID = "970309251"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Inisialisasi Groq (Akan bypass dengan selamat jika Key tiada)
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except:
    groq_client = None

# PARAMETER SWEET SPOT (LOCKED)
MC_MIN, MC_MAX = 5000000, 500000000
MIN_LIQUIDITY = 250000
MIN_VOL_MC_RATIO = 0.10
MIN_24H_CHANGE = 5.0
MAX_1H_CHANGE = -1.5
FIBO_ZONE = (0.5, 0.618)

SHARIAH_BLACKLIST = ['gambling', 'gamblefi', 'lending', 'borrowing', 'derivatives', 'perpetuals', 'adult']

# =====================================================================
# 2. MODUL SHARIAH & FILTRATION
# =====================================================================
def analyze_sweet_spot(coin_data):
    if not (MC_MIN <= coin_data['market_cap'] <= MC_MAX): return False
    if coin_data['liquidity'] < MIN_LIQUIDITY: return False
    # (Logik penuh filtering kau ada di sini)
    return True 

# =====================================================================
# 3. MODUL AI VIP INSIGHTS (GROQ - PERCUMA)
# =====================================================================
def get_ai_vip_report(coin):
    if not groq_client:
        return "⚠️ *AI Insight Standby:* Sila masukkan GROQ_API_KEY di Render."
        
    prompt = f"""
    Generate a professional crypto analysis for {coin['name']} (${coin['symbol']}).
    Language: Professional Malay mixed with English trading terms (Rojak style).
    Structure:
    1. Narrative & Catalyst: Kenapa sektor {coin['narrative']} hot. Compare dgn pesaing utama.
    2. Smart Money Intel: Mention 4 elite wallets (85% win-rate) accumulate. Social sentiment 'Mula Panas'.
    3. Execution Plan: Entry Zone (Fibo 0.5-0.618), TP 1, TP 2, TP 3, SL, and Risk/Reward Ratio (1:3.5).
    Keep it concise but high conviction.
    """
    
    try:
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a Senior Hedge Fund Analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        return response.choices[0].message.content
    except Exception as e:
        return "❌ *AI Insight Unavailable:* Isu sambungan ke pelayan Groq."

# =====================================================================
# 4. BROADCAST & INTERFACE
# =====================================================================
def send_signal(coin, verdict="STRONG BUY"):
    ai_report = get_ai_vip_report(coin)
    
    msg = f"""⚡ **ALPHA EXECUTION : {coin['narrative'].upper()}**

**Asset Identified:** {coin['name']} `${coin['symbol']}`
`{coin['contract_address']}`

📊 **MARKET METRICS**
   **Market Cap** : `${coin['market_cap'] / 1e6:.1f}M` | **Vol 24H** : `${coin['volume_24h'] / 1e6:.1f}M` 🟢
   **Trend 24H** : `+{coin['price_change_24h']}%` 🟢 | **1H Retracement** : `{coin['price_change_1h']}%` 🩸

📈 **TECHNICAL INTEL**
   **Momentum (1H)** : RSI {coin['rsi']} (Oversold Reset) 🟢 
   **Value Zone** : Fibonacci (0.5 - 0.618) 🎯

🌊 **ORDER FLOW SENSORS**
   **Net-Volume** : {verdict} 🟢 (${coin['buy_vol']}k In / ${coin['sell_vol']}k Out)
   **Capital Inflow**: `+{coin['flow_ratio']}x (Dominasi Institusi)`

{ai_report}

[ 🦄 Maestro ] [ 🟨 Binance ] [ 📰 Berita X ] [ 🐦 Twitter ] [ ✈️ Telegram ]
"""
    bot.send_message(VIP_CHANNEL_ID, msg, parse_mode="Markdown", disable_web_page_preview=True)

# =====================================================================
# 5. RENDER SERVER (ANTI-KILL & FIX 501 ERROR)
# =====================================================================
class RenderHandler(BaseHTTPRequestHandler):
    # Jawab isyarat GET
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"AlphaV3 Bot is Running Perfectly!")
        
    # JAWAB ISYARAT HEAD (INI YANG AKAN HILANGKAN TULISAN MERAH 501 TU!)
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
        
    # Supaya log tak semak (Block request log display)
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), RenderHandler)
    server.serve_forever()

# =====================================================================
# 6. MAIN LOOPS
# =====================================================================
def main_job():
    print(f"Scanning market... {datetime.now()}")

if __name__ == "__main__":
    # Start Dummy Server dalam thread (Wajib untuk Render Web Service)
    threading.Thread(target=run_server, daemon=True).start()
    
    try:
        bot.send_message(ADMIN_ID, "🚨 **SYSTEM REBOOTED**\nAlphaV3 beroperasi dengan Groq AI. Log Server telah dibersihkan.")
    except:
        pass
    
    schedule.every(15).minutes.do(main_job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
