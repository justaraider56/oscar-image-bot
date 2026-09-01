# $OSCAR & Shibutis Live Storyteller Bot

Bot Telegram 100 % autonome. Il surveille en temps réel les transactions des pairs $OSCAR et Shibutis sur Ethereum via l'API DexScreener et génère un récit automatique dans le chat à chaque achat.

## Variables d'environnement (Render)

- `TELEGRAM_TOKEN` : Jeton d'accès BotFather.
- `PAIR_ADDRESSES` : Adresses des pairs DexScreener séparées par une virgule (`0x...,0x...`).
- `CHAT_ID` : Identifiant du groupe Telegram (ex : `-100123456789`).
