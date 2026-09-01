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

# Photos de référence hébergées sur ton GitHub
REFERENCE_IMAGES = [
    "https://raw.githubusercontent.com/justaraider56/oscar-image-bot/main/ref1.jpg",
    "https://raw.githubusercontent.com/justaraider56/oscar-image-bot/main/ref2.jpg",
]

OSCAR_SCENES = [
    "flying a rocket to the moon with glowing blue Ethereum symbols, 3D render, high detail",
    "sitting in front of futuristic trading screens with green bullish charts, cinematic lighting",
    "wearing a cyberpunk armor suit in a neon city street at night, 8k resolution",
    "holding a massive glowing blue Ethereum crystal on gold coins, photorealistic",
    "wearing sunglasses in a penthouse overlooking a crypto skyscraper city"
]

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

async def generate_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = " ".join(context.args)
    ref_image = random.choice(REFERENCE_IMAGES)

    if user_input:
        prompt = f"In the exact style and character design of the reference image, {user_input}, highly detailed, 8k"
        caption_text = f"✨ **$OSCAR** : {user_input}"
    else:
        scene = random.choice(OSCAR_SCENES)
        prompt = f"In the exact style and character design of the reference image, {scene}"
        caption_text = "✨ **$OSCAR ETH** — Nouveau visuel IA"

    status_message = await update.message.reply_text("⏳ Génération d'une nouvelle variante $OSCAR...")

    try:
        encoded_prompt = urllib.parse.quote(prompt)
        encoded_ref = urllib.parse.quote(ref_image, safe="")
        seed = random.randint(1, 999999)

        # Appel img2img vers FLUX avec la photo de référence
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?image={encoded_ref}&width=1024&height=1024&seed={seed}&model=flux&nologo=true"

        response = requests.get(image_url, timeout=35)
        
        if response.status_code == 200:
            image_bytes = io.BytesIO(response.content)
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
            await update.message.reply_photo(
                photo=image_bytes, 
                caption=caption_text,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Serveur d'image occupé, réessaie dans un instant.")

    except Exception as e:
        print(f"Erreur : {e}")
        await update.message.reply_text("❌ Erreur lors de la génération.")

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
