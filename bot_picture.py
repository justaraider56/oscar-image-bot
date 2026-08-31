import os
import urllib.parse
import random
import requests
import io
import threading
import http.server
import socketserver
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

def start_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot OK")
        def log_message(self, format, *args):
            pass
    with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
        httpd.serve_forever()

# Description physique exacte du logo $OSCAR (Shiba Inu orange, sourcils blancs, regard déterminé)
OSCAR_BASE_PROMPT = "Oscar the crypto mascot, a fierce yellow-orange Shiba Inu dog head, prominent white eyebrows, intense black eyes, sharp ears, Ethereum ecosystem"

OSCAR_SCENES = [
    "holding a massive glowing blue Ethereum crystal on a pile of gold coins, 3D render",
    "flying a rocket to the moon with blue Ethereum symbols floating around, cinematic lighting",
    "sitting at a high-tech crypto trading desk with green candle charts on screen",
    "wearing a cyberpunk armor suit with glowing blue ETH logos, neon city backgroud",
    "standing proudly as a 3D mascot next to a giant reflective Ethereum octahedron",
    "wearing cool sunglasses in a luxury penthouse, crypto millionaire vibe, highly detailed"
]

async def generate_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = " ".join(context.args)

    if user_input:
        prompt_final = f"{OSCAR_BASE_PROMPT}, {user_input}, 3D digital art style, photorealistic lighting, 8k resolution, vibrant colors"
        caption_text = f"✨ **$OSCAR** : {user_input}"
    else:
        scene = random.choice(OSCAR_SCENES)
        prompt_final = f"{OSCAR_BASE_PROMPT}, {scene}, 3D digital art style, photorealistic lighting, 8k resolution"
        caption_text = "✨ **$OSCAR ETH** — Génération originale"

    status_message = await update.message.reply_text("⏳ Création du nouveau visuel $OSCAR...")

    try:
        encoded_prompt = urllib.parse.quote(prompt_final)
        seed = random.randint(1, 999999)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"

        response = requests.get(image_url, timeout=30)
        
        if response.status_code == 200:
            image_bytes = io.BytesIO(response.content)
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
            await update.message.reply_photo(
                photo=image_bytes, 
                caption=caption_text,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Serveur occupé, réessaie dans un instant.")

    except Exception as e:
        print(f"Erreur : {e}")
        await update.message.reply_text("❌ Erreur lors de la génération de l'image.")

def main():
    if not TELEGRAM_TOKEN:
        print("Erreur : Aucun token trouve.")
        return

    threading.Thread(target=start_dummy_server, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("picture", generate_picture))

    print("Bot $OSCAR en ligne !")
    app.run_polling()

if __name__ == "__main__":
    main()
