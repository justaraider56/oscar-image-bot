import os
import random
import threading
import urllib.parse
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Mini serveur HTTP pour valider le Web Service Gratuit de Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot OK")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# Récupère le token Telegram depuis l'environnement Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "TON_BOT_TOKEN_ICI")

DEFAULT_PROMPTS = [
    "Oscar the Shiba Inu dog jumping on a trampoline towards the Ethereum moon, cyberpunk style, digital art, highly detailed, 8k",
    "Oscar the Shiba Inu wearing a futuristic space suit exploring an Ethereum galaxy, cinematic lighting, octane render",
    "Golden statue of Oscar the Shiba Inu holding an Ethereum crystal in a futuristic neon city, hyperrealistic, 3d render",
    "Vintage 1980s retro comic book cover featuring Oscar the Shiba Inu, text 'ALL HAIL THE SHIBA', detailed artwork",
    "Oscar the Shiba Inu dog sitting on a throne of gold and Ethereum coins, baroque oil painting style, highly detailed"
]

async def picture_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("🎨 **Génération de l'image $OSCAR en cours...**", parse_mode="Markdown")

    if context.args:
        user_input = " ".join(context.args)
        full_prompt = f"Oscar Shiba Inu dog, {user_input}, Ethereum theme, highly detailed, digital art, 8k"
    else:
        user_input = None
        full_prompt = random.choice(DEFAULT_PROMPTS)

    try:
        encoded_prompt = urllib.parse.quote(full_prompt)
        seed = random.randint(1, 999999)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1024&height=1024&nologo=true"

        response = requests.get(image_url, timeout=35)
        
        if response.status_code == 200:
            image_bytes = response.content
            caption_text = (
                f"✨ **Prompt :** _{user_input if user_input else 'Génération aléatoire $OSCAR'}_\n\n"
                f"🚀 *Propulsé par Oscar Generative Engine*"
            )

            await update.message.reply_photo(
                photo=image_bytes,
                caption=caption_text,
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Erreur lors de la génération. Le serveur IA est indisponible.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Une erreur est survenue : `{str(e)}`", parse_mode="Markdown")

if __name__ == "__main__":
    # Lancement du serveur Web en arrière-plan pour Render
    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler(["picture", "image", "oscar"], picture_handler))
    print("Bot $OSCAR en ligne et prêt !")
    app.run_polling()
