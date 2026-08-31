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

# Serveur HTTP en arrière-plan pour satisfaire le test de port Render
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

OSCAR_SCENES = [
    "holding a massive glowing blue Ethereum diamond on a pile of gold coins",
    "flying a rocket with '$OSCAR' logo directly to a giant physical moon",
    "sitting in front of a futuristic multi-monitor trading desk, bullish charts on screen",
    "wearing a cyber suit with glowing blue ETH symbols, walking through a neon city",
    "as a 3D mascot standing proudly on a large, reflective Ethereum octahedron",
    "in a classic cartoon style, celebrating a '100x' profit chart"
]

async def generate_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = " ".join(context.args)

    if user_input:
        prompt_final = f"Oscar character, $OSCAR Ethereum crypto mascot, {user_input}, photorealistic, 8k resolution, highly detailed, vibrant colors"
        caption_text = f"✨ **$OSCAR** : {user_input}"
    else:
        scene = random.choice(OSCAR_SCENES)
        prompt_final = f"Oscar character, $OSCAR Ethereum crypto mascot, {scene}, photorealistic, 8k resolution, highly detailed, vibrant colors"
        caption_text = "✨ **$OSCAR ETH** — Génération aléatoire"

    status_message = await update.message.reply_text("⏳ Création de l'image $OSCAR...")

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

    # Lancement du serveur Web pour Render
    threading.Thread(target=start_dummy_server, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("picture", generate_picture))

    print("Bot $OSCAR en ligne !")
    app.run_polling()

if __name__ == "__main__":
    main()
