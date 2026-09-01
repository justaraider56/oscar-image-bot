import os
import asyncio
import threading
import requests
import http.server
import socketserver
from telegram.ext import ApplicationBuilder, Application

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

OSCAR_PAIR = os.environ.get("OSCAR_PAIR", "").lower()
SHIBUTIS_CA = os.environ.get("SHIBUTIS_CA", "").lower()

def start_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot AI Storyteller OK")
        def log_message(self, format, *args):
            pass
    try:
        with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Erreur serveur HTTP : {e}")

def format_number(num):
    """Formatte les grands nombres (ex: 150000 -> 150K$)."""
    try:
        val = float(num)
        if val >= 1_000_000:
            return f"${val / 1_000_000:.2f}M"
        if val >= 1_000:
            return f"${val / 1_000:.1f}K"
        return f"${val:.2f}"
    except (ValueError, TypeError):
        return "N/A"

def generate_ai_story(context_event):
    """Génère une punchline décalée et fun via Gemini."""
    if not GEMINI_API_KEY:
        return "🚨 **ALERTE BOUGIE VERTE !** Quelqu'un vient de faire chauffer la carte bleue !"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = (
        "Tu es Oscar, la mascotte bouledogue/chien de garde complètement déjantée, drôle et hyper enthousiaste du projet crypto $OSCAR. "
        "Rédige une réaction ultra courte (1 à 2 phrases max) pour fêter un nouvel achat sur Telegram. "
        "Utilise du vocabulaire crypto/degen fun (bougie verte, to the moon, bag, meute, croquettes de luxe), des emojis, et reste très percutant. "
        f"Contexte : {context_event}. "
        "Ne mets JAMAIS de guillemets autour de ton texte."
    )

    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=8)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                text = candidates[0]["content"]["parts"][0]["text"]
                return text.strip()
    except Exception as e:
        print(f"Erreur génération IA : {e}")

    return "🟢 **GROS ACHAT EN COURS !** Oscar remue la queue, les bougies vertes arrivent !"

async def track_oscar(app, last_state):
    if not OSCAR_PAIR:
        return
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/ethereum/{OSCAR_PAIR}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            pairs = data.get("pairs") or []
            if pairs:
                pair = pairs[0]
                buys = pair.get("txns", {}).get("h1", {}).get("buys", 0)
                price = pair.get("priceUsd", "N/A")
                mcap = pair.get("fdv") or pair.get("marketCap", 0)
                vol24 = pair.get("volume", {}).get("h24", 0)

                if last_state["oscar_buys"] is not None and buys > last_state["oscar_buys"]:
                    ai_punchline = generate_ai_story(f"Nouvel achat $OSCAR ! Prix: ${price}, Market Cap: {format_number(mcap)}")
                    
                    msg = (
                        f"{ai_punchline}\n\n"
                        f"📊 **Météo du Token $OSCAR :**\n"
                        f"💵 **Prix :** `${price}`\n"
                        f"🧢 **Market Cap :** `{format_number(mcap)}`\n"
                        f"🔥 **Vol 24h :** `{format_number(vol24)}`"
                    )
                    
                    if CHAT_ID:
                        await app.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

                last_state["oscar_buys"] = buys
    except Exception as e:
        print(f"Erreur suivi $OSCAR : {e}")

async def track_shibutis(app, last_state):
    if not SHIBUTIS_CA:
        return
    try:
        url = f"https://api.reservoir.tools/sales/v6?collection={SHIBUTIS_CA}&limit=1"
        headers = {"accept": "*/*"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            sales = res.json().get("sales", [])
            if sales:
                latest_sale = sales[0]
                sale_id = latest_sale.get("id")
                price_eth = latest_sale.get("price", {}).get("amount", {}).get("decimal", "N/A")
                token_id = latest_sale.get("token", {}).get("tokenId", "?")

                if last_state["last_nft_sale_id"] is not None and sale_id != last_state["last_nft_sale_id"]:
                    ai_punchline = generate_ai_story(f"Vente du NFT Shibuti #{token_id} pour {price_eth} ETH")
                    
                    msg = (
                        f"{ai_punchline}\n\n"
                        f"🖼️ **Shibuti #{token_id}** adopté !\n"
                        f"💎 **Prix de vente :** `{price_eth} ETH`"
                    )
                    
                    if CHAT_ID:
                        await app.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

                last_state["last_nft_sale_id"] = sale_id
    except Exception as e:
        print(f"Erreur suivi Shibutis NFT : {e}")

async def main_loop(app: Application):
    last_state = {"oscar_buys": None, "last_nft_sale_id": None}
    while True:
        await track_oscar(app, last_state)
        await track_shibutis(app, last_state)
        await asyncio.sleep(30)

async def post_init(app: Application):
    asyncio.create_task(main_loop(app))

def main():
    if not TELEGRAM_TOKEN:
        print("Erreur : TELEGRAM_TOKEN manquant.")
        return

    threading.Thread(target=start_dummy_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    print("Bot AI Storyteller prêt !")
    app.run_polling()

if __name__ == "__main__":
    main()
