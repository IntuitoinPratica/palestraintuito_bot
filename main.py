import logging
import pickle
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

# 🔐 TOKEN da variabile ambiente
TOKEN = os.getenv("BOT_TOKEN")

# 📁 Caricamento utenti salvati
if os.path.exists("utenti.pkl"):
    try:
        with open("utenti.pkl", "rb") as f:
            utenti = pickle.load(f)
    except Exception:
        utenti = {}
else:
    utenti = {}

# 🧠 Logging
logging.basicConfig(level=logging.INFO)

# ⏱️ Scheduler globale
scheduler = BackgroundScheduler()
scheduler.start()

# 📖 Caricamento contenuto del giorno
def carica_contenuto(giorno):
    path = f"contenuti/Giorno_{giorno:02d}.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return "Hai completato tutti i 15 giorni della Palestra Intuito. Grazie per aver camminato con noi! 🌟"

# ✉️ Invio contenuto
async def invia_contenuto(application, user_id, giorno):
    testo = carica_contenuto(giorno)
    await application.bot.send_message(chat_id=user_id, text=testo)

# 🧘‍♀️ /start per nuovi iscritti
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    utenti[user_id] = {
        "giorno": 1,
        "prossimo": datetime.now() + timedelta(days=1)
    }

    await update.message.reply_text(
        "🌟 Benvenutə nella *Palestra Intuito*! Da oggi riceverai ogni giorno un contenuto ispirazionale per ascoltarti più a fondo.\n\n✨ Iniziamo subito con il Giorno 1!"
    )

    await invia_contenuto(context.application, user_id, 1)

    with open("utenti.pkl", "wb") as f:
        pickle.dump(utenti, f)

    # Rimuovi job duplicato se esiste
    if scheduler.get_job(str(user_id)):
        scheduler.remove_job(str(user_id))

    # Programma invio quotidiano
    scheduler.add_job(
        invio_giornaliero,
        trigger='interval',
        days=1,
        args=[context.application],
        id=str(user_id),
        next_run_time=utenti[user_id]["prossimo"]
    )

# ⏰ Invio giornaliero automatico
async def invio_giornaliero(application):
    for user_id in list(utenti.keys()):
        utenti[user_id]["giorno"] += 1
        utenti[user_id]["prossimo"] = datetime.now() + timedelta(days=1)

        giorno = utenti[user_id]["giorno"]
        if giorno <= 15:
            await invia_contenuto(application, user_id, giorno)
        else:
            logging.info(f"L'utente {user_id} ha completato tutti i 15 giorni.")

    with open("utenti.pkl", "wb") as f:
        pickle.dump(utenti, f)

# 🔁 Comando /next per invio manuale del giorno successivo
async def next_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in utenti:
        utenti[user_id]["giorno"] += 1
        utenti[user_id]["prossimo"] = datetime.now() + timedelta(days=1)
        giorno = utenti[user_id]["giorno"]

        if giorno <= 15:
            await update.message.reply_text(f"✨ Ecco il tuo contenuto del Giorno {giorno}:")
            await invia_contenuto(context.application, user_id, giorno)
        else:
            await update.message.reply_text("✅ Hai già completato tutti i 15 giorni! Bravissima 🌟")

        with open("utenti.pkl", "wb") as f:
            pickle.dump(utenti, f)
    else:
        await update.message.reply_text("❗Non sei ancora iscrittə! Usa /start per iniziare 🌱")

# 🚀 Avvio bot con webhook
if __name__ == '__main__':
    if TOKEN is None:
        print("❌ ERRORE: BOT_TOKEN non trovato.")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("next", next_day))
        print("✅ Bot avviato con successo!")

        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get('PORT', 8443)),
            webhook_url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/webhook"
        )
