import os
import random
import asyncio
import threading
import requests
import http.server
import socketserver
from telegram.ext import ApplicationBuilder

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Adresses
OSCAR_PAIR = os.environ.get("OSCAR_PAIR", "").lower()      # Pair Address DexScreener
SHIBUTIS_CA = os.environ.get("SHIBUTIS_CA", "").lower()    # Contract Address du NFT

STORIES_OSCAR = [
    "🐾 **$OSCAR :** Un nouveau membre vient de rejoindre la meute ! La réserve d'Ethereum grandit.",
    "⚡ **$OSCAR :** Achat confirmé sur la blockchain. La poussée continue !",
    "🐋 **$OSCAR :** Mouvement de baleine détecté ! Les fondations d'Oscar tremblent !"
]

STORIES_SHIBUTIS = [
    "🎨 **Shibutis NFT :** Un nouveau Shibuti vient de trouver un acquéreur !",
    "🔥 **Shibutis NFT :** Une nouvelle vente vient d'avoir lieu sur les marketplaces !",
    "✨ **Shibutis NFT :** La collection prend de la valeur, transaction confirmée !"
]

def start_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot Storyteller Token + NFT OK")
        def log_message(self, format, *args):
            pass
    with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
        httpd.serve_forever()

async def track_oscar(app, last_state):
    """Vérifie les achats du token $OSCAR via DexScreener."""
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

                if last_state["oscar_buys"] is not None and buys > last_state["oscar_buys"]:
                    story = random.choice(STORIES_OSCAR)
                    msg = f"{story}\n\n💰 **Prix $OSCAR :** ${price}"
                    if CHAT_ID:
                        await app.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

                last_state["oscar_buys"] = buys
    except Exception as e:
        print(f"Erreur suivi $OSCAR : {e}")

async def track_shibutis(app, last_state):
    """Vérifie les ventes NFT Shibutis via Reservoir."""
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
                    story = random.choice(STORIES_SHIBUTIS)
                    msg = f"{story}\n\n🖼️ **Shibuti #{token_id}** acheté pour **{price_eth} ETH** !"
                    if CHAT_ID:
                        await app.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

                last_state["last_nft_sale_id"] = sale_id
    except Exception as e:
        print(f"Erreur suivi Shibutis NFT : {e}")

async def main_loop(app):
    last_state = {"oscar_buys": None, "last_nft_sale_id": None}
    while True:
        await track_oscar(app, last_state)
        await track_shibutis(app, last_state)
        await asyncio.sleep(30)

def main():
    if not TELEGRAM_TOKEN:
        print("Erreur : TELEGRAM_TOKEN manquant.")
        return

    threading.Thread(target=start_dummy_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    loop = asyncio.get_event_loop()
    loop.create_task(main_loop(app))

    print("Bot Token + NFT en ligne !")
    app.run_polling()

if __name__ == "__main__":
    main()
