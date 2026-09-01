import os
import random
import asyncio
import threading
import requests
import http.server
import socketserver
from telegram.ext import ApplicationBuilder

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# Met tes adresses de pairs séparées par une virgule (ex: 0xOscar...,0xShibutis...)
PAIR_ADDRESSES = os.environ.get("PAIR_ADDRESSES", "")
CHAT_ID = os.environ.get("CHAT_ID")

# Récits personnalisés selon le projet qui génère l'achat
STORIES = {
    "OSCAR": [
        "🐾 **$OSCAR :** Un nouveau membre vient de rejoindre la meute ! La réserve d'Ethereum grandit.",
        "⚡ **$OSCAR :** Achat confirmé sur la blockchain. La poussée continue !",
        "🐋 **$OSCAR :** Mouvement de baleine détecté ! Les fondations d'Oscar tremblent !"
    ],
    "SHIBUTIS": [
        "🎨 **Shibutis :** Nouvelle transaction sur la collection ! Un Shibuti vient d'entrer en jeu.",
        "🔥 **Shibutis :** L'écosystème prend de la valeur, nouvel achat validé !",
        "✨ **Shibutis :** Signal on-chain détecté pour la meute Shibutis !"
    ]
}

def start_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot Storyteller Multi-CA OK")
        def log_message(self, format, *args):
            pass
    with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
        httpd.serve_forever()

async def track_onchain_activity(app):
    """Vérifie plusieurs pairs DexScreener toutes les 30 secondes."""
    last_tx_counts = {}

    if not PAIR_ADDRESSES:
        print("Erreur : Aucune adresse configurée dans PAIR_ADDRESSES.")
        return

    # Nettoyage et formatage de la liste d'adresses
    pairs_list = [p.strip().lower() for p in PAIR_ADDRESSES.split(",") if p.strip()]
    url = f"https://api.dexscreener.com/latest/dex/pairs/ethereum/{','.join(pairs_list)}"

    while True:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                pairs = data.get("pairs") or []

                for pair in pairs:
                    pair_addr = pair.get("pairAddress", "").lower()
                    base_symbol = pair.get("baseToken", {}).get("symbol", "TOKEN").upper()
                    buys = pair.get("txns", {}).get("h1", {}).get("buys", 0)
                    price = pair.get("priceUsd", "N/A")

                    # Initialisation au premier passage
                    if pair_addr not in last_tx_counts:
                        last_tx_counts[pair_addr] = buys
                        continue

                    # Détection d'un nouvel achat
                    if buys > last_tx_counts[pair_addr]:
                        project_key = "SHIBUTIS" if "SHIBUTI" in base_symbol else "OSCAR"
                        story_list = STORIES.get(project_key, STORIES["OSCAR"])
                        story = random.choice(story_list)

                        caption = f"{story}\n\n💰 **Prix actuel ({base_symbol}) :** ${price}"

                        if CHAT_ID:
                            await app.bot.send_message(
                                chat_id=CHAT_ID,
                                text=caption,
                                parse_mode="Markdown"
                            )

                        last_tx_counts[pair_addr] = buys
        except Exception as e:
            print(f"Erreur lors du suivi multi-CA : {e}")

        await asyncio.sleep(30)

def main():
    if not TELEGRAM_TOKEN:
        print("Erreur : TELEGRAM_TOKEN manquant.")
        return

    threading.Thread(target=start_dummy_server, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    loop = asyncio.get_event_loop()
    loop.create_task(track_onchain_activity(app))

    print("Bot Storyteller Multi-CA en ligne !")
    app.run_polling()

if __name__ == "__main__":
    main()
