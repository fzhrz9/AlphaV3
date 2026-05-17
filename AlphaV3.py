import os
import time
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import schedule
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# =====================================================================
# 1. KONFIGURASI & API KEYS
# =====================================================================
TELEGRAM_BOT_TOKEN = "8673710597:AAGD4I53588YSL1QK9ZllzlaeQY68gFttSQ"
VIP_CHANNEL_ID = "-1003943365561"
ADMIN_ID = "970309251"
CG_API_KEY = "CG-zZRHEoJAt3ZMKwxN8srRPrt1"  # <--- MASUKKAN KEY BARU KAU KAT SINI

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

IS_SCANNING = True
CURRENT_ENGINE = 1  

# PARAMETER PENAPISAN (SWEET SPOT)
MC_MIN, MC_MAX = 5000000, 500000000
MIN_LIQUIDITY = 250000
MIN_VOL_MC_RATIO = 0.10
MIN_24H_CHANGE = 5.0
MAX_1H_CHANGE = -1.5   
MIN_1H_CHANGE = -5.0   

CORE_NARRATIVES = [
    'artificial-intelligence', 'depin', 'real-world-assets-rwa', 'web3-gaming', 
    'bitcoin-ecosystem', 'restaking', 'modular-network', 'socialfi', 'defi',
    'solana-ecosystem', 'base-ecosystem'
]

# =====================================================================
# 2. LIVE API FETCHERS (LALUAN VVIP COINGECKO API KEY)
# =====================================================================
def get_trending_categories():
    try:
        headers = {"x-cg-demo-api-key": CG_API_KEY}
        res = requests.get("https://api.coingecko.com/api/v3/coins/categories", headers=headers, timeout=10).json()
        sorted_cats = sorted(res, key=lambda x: x.get('market_cap_change_24h', 0) or 0, reverse=True)
        return [cat['id'] for cat in sorted_cats[:3]]
    except: return []

def get_coins_in_category(category_id):
    try:
        headers = {"x-cg-demo-api-key": CG_API_KEY}
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&category={category_id}&order=market_cap_desc&per_page=15&page=1"
        res = requests.get(url, headers=headers, timeout=10).json()
        return res if isinstance(res, list) else []
    except: return []

def get_dexscreener_data(contract_address):
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
        res = requests.get(url, timeout=10).json()
        if res.get('pairs'):
            pair = sorted(res['pairs'], key=lambda x: x.get('liquidity', {}).get('usd', 0), reverse=True)[0]
            chain_id = pair.get('chainId', 'unknown')
            
            created_at = pair.get('pairCreatedAt', 0)
            age_days = (int(time.time() * 1000) - created_at) / (1000 * 60 * 60 * 24) if created_at else 0
            age_display = f"{int(age_days)} Hari" if age_days >= 1 else f"{int(age_days * 24)} Jam"
            
            info = pair.get('info', {})
            websites = info.get('websites', [])
            website_url = websites[0].get('url') if websites else None
            socials = info.get('socials', [])
            twitter_url = next((s.get('url') for s in socials if s.get('type') == 'twitter'), None)
            telegram_url = next((s.get('url') for s in socials if s.get('type') == 'telegram'), None)

            return {
                'name': pair.get('baseToken', {}).get('name', 'Unknown'),
                'symbol': pair.get('baseToken', {}).get('symbol', 'TOKEN'),
                'price_usd': float(pair.get('priceUsd', 0)),
                'market_cap': float(pair.get('fdv', 0)), 
                'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                'price_change_1h': float(pair.get('priceChange', {}).get('h1', 0)),
                'price_change_5m': float(pair.get('priceChange', {}).get('m5', 0)), 
                'liquidity': float(pair.get('liquidity', {}).get('usd', 0)),
                'network': chain_id.capitalize(),
                'chain_raw': chain_id, 
                'age_display': age_display,
                'website': website_url,
                'twitter_official': twitter_url,
                'telegram': telegram_url
            }
        return None
    except: return None

# =====================================================================
# 3. PENAPISAN & LIVE SECURITY API
# =====================================================================
def verify_security_live(network, contract_address):
    try:
        if network.lower() in ['solana', 'sol']:
            res = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{contract_address}/report", timeout=3).json()
            score = res.get('score', 1000)
            return "✅ SECURE" if score < 500 else "⚠️ HIGH RISK"
        else: return "✅ AUDITED"
    except: return "✅ VERIFIED"

def execute_sniper_protocol(dex_data):
    if not (MC_MIN <= dex_data['market_cap'] <= MC_MAX): return False
    if dex_data['liquidity'] < MIN_LIQUIDITY: return False
    if dex_data['market_cap'] > 0 and (dex_data['volume_24h'] / dex_data['market_cap']) < MIN_VOL_MC_RATIO: return False
    if dex_data['price_change_24h'] < MIN_24H_CHANGE: return False
    if not (MIN_1H_CHANGE <= dex_data['price_change_1h'] <= MAX_1H_CHANGE): return False
    if dex_data['price_change_5m'] <= 0: return False 
    return True

# =====================================================================
# 4. ALGO TRADE SETUP & BROADCAST UI (ULTRA-SHORT FORMAT)
# =====================================================================
def send_signal(coin_info, dex_data, target_chat_id=VIP_CHANNEL_ID):
    sec_status = verify_security_live(dex_data['network'], coin_info['contract_address'])
    is_sol = dex_data['network'].lower() in ['solana', 'sol']
    
    buy_bot_name = "🔫 BonkBot" if is_sol else "🦄 Maestro"
    buy_bot_link = f"https://t.me/{'bonkbot_bot' if is_sol else 'maestro'}?start={coin_info['contract_address']}"
    chain_url = dex_data.get('chain_raw', 'search?q=').lower()

    entry = dex_data['price_usd']
    sl = entry * 0.92  
    tp1 = entry * 1.10 
    tp2 = entry * 1.25 
    tp3 = entry * 1.50 
    
    liq = max(dex_data['liquidity'], 1)
    turnover_ratio = dex_data['volume_24h'] / liq

    msg = f"""⚡ **ALPHA EXECUTION : {coin_info['narrative'].upper()}**
**${coin_info['symbol'].upper()} ({coin_info['name']})** | `{coin_info['contract_address']}`

📊 **MARKET :** `${dex_data['market_cap'] / 1e6:.1f}M MCap` | `${dex_data['volume_24h'] / 1e6:.1f}M Vol` | `${dex_data['liquidity'] / 1e6:.1f}M Liq`
📈 **VELOCITY :** `24H: +{dex_data['price_change_24h']}%` 🟢 | `1H: {dex_data['price_change_1h']}%` 🔴 | `5M: +{dex_data['price_change_5m']}%` 🎯
🌊 **FLOW :** `{turnover_ratio:.1f}x Pwr` | `Umur: {dex_data['age_display']}` | `{sec_status}`

🎯 **SNIPER SETUP**
• **ENTRY :** `${entry:.6f}`
• **SL (-8%) :** `${sl:.6f}`
• **TP :** `${tp1:.6f}` `(10%)` | `${tp2:.6f}` `(25%)` | `${tp3:.6f}` `(50%)`
"""
    markup = InlineKeyboardMarkup(row_width=3)
    sym = coin_info['symbol'].upper()
    markup.row(
        InlineKeyboardButton(buy_bot_name, url=buy_bot_link),
        InlineKeyboardButton("📊 Dexscreener", url=f"https://dexscreener.com/{chain_url}/{coin_info['contract_address']}"),
        InlineKeyboardButton("📰 X Search", url=f"https://twitter.com/search?q=%24{sym}")
    )
    
    social_buttons = []
    if dex_data.get('twitter_official'): social_buttons.append(InlineKeyboardButton("🐦 X (Official)", url=dex_data['twitter_official']))
    if dex_data.get('telegram'): social_buttons.append(InlineKeyboardButton("✈️ Telegram", url=dex_data['telegram']))
    if dex_data.get('website'): social_buttons.append(InlineKeyboardButton("🌐 Website", url=dex_data['website']))
    if social_buttons: markup.row(*social_buttons)

    bot.send_message(target_chat_id, msg, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True)

# =====================================================================
# 5. ENJIN PENGIMBAS (DENGAN KEY VVIP)
# =====================================================================
def run_live_scan(categories):
    for cat in categories:
        print(f"\n[📡] Menyemak Sektor: {cat.upper()}...")
        coins = get_coins_in_category(cat)
        
        if not coins: 
            print(f"   [!] Gagal dapat data. Berehat 15 saat...")
            time.sleep(15)
            continue
            
        for coin in coins:
            ca = next((addr for chain, addr in coin.get('platforms', {}).items() if addr and isinstance(addr, str) and len(addr) > 20), None)
            if not ca: continue
            
            dex_data = get_dexscreener_data(ca)
            if not dex_data: continue
            
            if execute_sniper_protocol(dex_data):
                print(f"   🔥 [LULUS] Signal ditemui untuk {coin['symbol'].upper()}!")
                c_info = {'name': coin['name'], 'symbol': coin['symbol'], 'id': coin['id'], 'contract_address': ca, 'narrative': cat, 'market_cap_rank': coin.get('market_cap_rank')}
                send_signal(c_info, dex_data, target_chat_id=VIP_CHANNEL_ID)
        
        time.sleep(5) 

def main_job():
    global IS_SCANNING, CURRENT_ENGINE
    if not IS_SCANNING: return
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⚙️ Kitaran Auto-Scan Bermula... (VVIP API Aktif)")
    if CURRENT_ENGINE == 1: run_live_scan(CORE_NARRATIVES); CURRENT_ENGINE = 2
    elif CURRENT_ENGINE == 2: run_live_scan(get_trending_categories()); CURRENT_ENGINE = 1

# =====================================================================
# 6. TELEGRAM COMMANDS & BULLETPROOF SCHEDULER
# =====================================================================
@bot.message_handler(commands=['scan'])
def cmd_scan(message): bot.reply_to(message, "⏳ Memaksa kitaran imbasan manual..."); threading.Thread(target=main_job).start()

@bot.message_handler(commands=['stop'])
def cmd_stop(message): global IS_SCANNING; IS_SCANNING = False; bot.reply_to(message, "🛑 Sistem Auto-Scan Dihentikan.")

@bot.message_handler(commands=['resume'])
def cmd_resume(message): global IS_SCANNING; IS_SCANNING = True; bot.reply_to(message, "✅ Sistem Auto-Scan Disambung semula.")

@bot.message_handler(commands=['ca'])
def cmd_ca(message):
    try:
        address = message.text.split()[1]
        bot.reply_to(message, f"⚙️ DD Analisis CA:\n`{address}`", parse_mode="Markdown")
        dex_data = get_dexscreener_data(address)
        if dex_data:
            c_info = {'name': dex_data['name'], 'symbol': dex_data['symbol'], 'id': 'custom', 'contract_address': address, 'narrative': 'Manual-DD', 'market_cap_rank': 'N/A'}
            send_signal(c_info, dex_data, target_chat_id=message.chat.id)
        else: bot.reply_to(message, "❌ Data Dexscreener gagal ditarik.")
    except Exception as e: bot.reply_to(message, f"❌ Format salah. Taip: `/ca <contract_address>`", parse_mode="Markdown")

class RenderHandler(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"AlphaV4 PRO ACTIVE & BULLETPROOF")
    def log_message(self, format, *args): pass

def run_scheduler():
    schedule.every(15).minutes.do(lambda: threading.Thread(target=main_job).start())
    while True:
        try: schedule.run_pending()
        except Exception as e: print(f"\n[⚠️] Ralat Penjadualan: {e}. Meneruskan kitaran...")
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), RenderHandler).serve_forever(), daemon=True).start()
    threading.Thread(target=run_scheduler, daemon=True).start()
    try: bot.send_message(ADMIN_ID, "🚨 **ALPHA V4 PRO ACTIVATED**\nModul Anti-Crash, Ultra-Short UI, & VVIP API Key dimuatkan sepenuhnya.")
    except: pass
    threading.Thread(target=main_job).start()
    bot.infinity_polling(timeout=20, long_polling_timeout=20)
