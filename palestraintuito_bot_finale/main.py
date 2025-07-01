import logging
import pickle
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

# TOKEN Telegram
TOKEN = os.getenv("BOT_TOKEN")

# Caricamento utenti salvati (se esistono)
if os.path.exists("utenti.pkl"):
    with open("utenti.pkl", "rb") as f:
        utenti = pickle.load(f)
else:
    utenti = {}

# Logging
logging.basicConfig(level=logging.INFO)

# Avvio Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Carica il contenuto del giorno (se esiste il file)
def carica_contenuto(giorno):
    path = f"contenuti/Giorno_{giorno:02d}.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        print(f"[ATTENZIONE] File Giorno_{giorno:02d}.txt non trovato.")
        return None

# Invia il contenuto se disponibile
async def invia_contenuto(application, user_id, giorno):
    testo = carica_contenuto(giorno)
    if testo:  # solo se esiste
        await application.bot.send_message(chat_id=user_id, text=testo)

# Comando /start: parte dal Giorno 1
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    utenti[user_id] = {"giorno": 1, "prossimo": datetime.now() + timedelta(days=1)}
    await update.message.reply_text(
        "🌟 Benvenutə nella *Palestra Intuito*! Da oggi riceverai ogni giorno un contenuto ispirazionale per ascoltarti più a fondo.\n\n✨ Iniziamo subito con il Giorno 1!"
    )
    await invia_contenuto(context.application, user_id, 1)
    scheduler.add_job(
        invio_giornaliero,
        'interval',
        days=1,
        args=[context.application],
        id=str(user_id),
        next_run_time=utenti[user_id]["prossimo"]
    )

# Invio automatico quotidiano
async def invio_giornaliero(application):
    for user_id in utenti:
        utenti[user_id]["giorno"] += 1
        utenti[user_id]["prossimo"] = datetime.now() + timedelta(days=1)
        giorno = utenti[user_id]["giorno"]
        if giorno <= 15:
            await invia_contenuto(application, user_id, giorno)
    # Salva lo stato
    with open("utenti.pkl", "wb") as f:
        pickle.dump(utenti, f)

# Avvio del bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
