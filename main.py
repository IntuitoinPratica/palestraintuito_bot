import logging
import pickle
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

# 🔐 TOKEN Telegram da variabile ambiente (Render)
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

# 📖 Funzione per caricare il contenuto del giorno
def carica_contenuto(giorno):
    path = f"contenuti/Giorno_{giorno:02d}.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return "Hai completato tutti i giorni della Palestra Intuito. Grazie per aver camminato con noi! 🌟"

# ✉️ Invio del contenuto al singolo utente
async def invia_contenuto(application, user_id, giorno):
    testo = carica_contenuto(giorno)
    await application.bot.send_message(chat_id=user_id, text=testo)

# 🧘‍♀️ Comando /start per ogni nuovo iscritto
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Aggiorna o aggiungi l’utente
    utenti[user_id] = {
        "giorno": 1,
        "prossimo": datetime.now() + timedelta(days=1)
    }

    await update.message.reply_text(
        "🌟 Benvenutə nella *Palestra Intuito*! Da oggi riceverai ogni giorno un contenuto ispirazionale per ascoltarti più a fondo.\n\n✨ Iniziamo subito con il Giorno 1!"
    )

    await invia_contenuto(context.application, user_id, 1)

    # Salva dati utente
    with open("utenti.pkl", "wb") as f:
        pickle.dump(utenti, f)

    # Rimuovi job duplicato se esiste
    if scheduler.get_job(str(user_id)):
        scheduler.remove_job(str(user_id))

    # Programma l’invio quotidiano
    scheduler.add_job(
        invio_giornaliero,
        trigger='interval',
        days=1,
        args=[context.application],
        id=str(user_id),
        next_run_time=utenti[user_id]["prossimo"]
    )

# 🚀 Invio automatico quotidiano per tutti
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

# 🎯 Avvio del bot
if __name__ == '__main__':
    if TOKEN is None:
        print("❌ ERRORE: BOT_TOKEN non trovato nelle variabili ambiente.")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        print("✅ Bot avviato con successo!")
        app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get('PORT', 8443)),
    webhook_url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/webhook"
)

