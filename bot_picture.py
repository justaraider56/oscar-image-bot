import os
import urllib.parse
import random
import requests
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Récupération du token Telegram depuis l'environnement ou la commande
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def generate_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Génère une image gratuite et ultra-réaliste avec FLUX (Pollinations)"""
    
    prompt_user = " ".join(context.args)
    if not prompt_user:
        await update.message.reply_text(
            "❌ Ajoute une description !\nExemple : `/picture un portrait photo d'un vieux marin au bord de la mer, 8k`",
            parse_mode="Markdown"
        )
        return

    # Message d'attente
    status_message = await update.message.reply_text(f"⏳ Génération en cours pour : \"{prompt_user}\"...")

    try:
        # 1. On améliore le prompt pour forcer le réalisme et la qualité
        enhanced_prompt = f"{prompt_user}, photorealistic, 8k resolution, highly detailed, professional photography, realistic lighting"
        
        # 2. Encodage du texte pour l'URL
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        
        # 3. Graine aléatoire (seed) pour que deux demandes identiques donnent des images différentes
        seed = random.randint(1, 999999)
        
        # 4. URL de l'API gratuite Pollinations (Modèle FLUX)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"

        # 5. Téléchargement de l'image
        response = requests.get(image_url, timeout=30)
        
        if response.status_code == 200:
            image_bytes = io.BytesIO(response.content)
            
            # Supprimer le message "Génération en cours..."
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
            
            # Envoyer l'image générée
            await update.message.reply_photo(photo=image_bytes, caption=f"📸 {prompt_user}")
        else:
            await update.message.reply_text("❌ Impossible de générer l'image pour le moment, réessaie dans un instant.")

    except Exception as e:
        print(f"Erreur lors de la génération : {e}")
        await update.message.reply_text("❌ Une erreur est survenue lors de la création de l'image.")


def main():
    if not TELEGRAM_TOKEN:
        print("Erreur : Aucun token Telegram trouvé.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Commande /picture
    app.add_handler(CommandHandler("picture", generate_picture))

    print("Bot en ligne et prêt !")
    app.run_polling()

if __name__ == "__main__":
    main()
