import os
import requests
import telegram
from flask import Flask, request
import random # Kita akan gunakan ini untuk membuat hasil dummy

# --- Konfigurasi dari Environment Variables ---
# Kita tetap membutuhkan token dan URL aplikasi
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
APP_URL = os.environ.get('APP_URL')

# --- Inisialisasi Aplikasi Flask dan Bot Telegram ---
app = Flask(__name__)
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# --- FUNGSI PREDIKSI PALSU (DUMMY) ---
# Fungsi ini tidak menggunakan AI. Ia hanya mengembalikan hasil yang sudah disiapkan.
def dummy_predict_and_recommend(image_path):
    # Daftar kemungkinan hasil palsu
    dummy_results = [
        {
            'penyakit_terdeteksi': 'Tomato_Healthy',
            'keyakinan': "98.75%",
            'penanganan': 'Tanaman tampak sehat. Lanjutkan perawatan rutin.',
            'rekomendasi_pestisida': 'Tidak perlu.',
            'info_lain': 'Ini adalah hasil dummy untuk keperluan testing.'
        },
        {
            'penyakit_terdeteksi': 'Tomato_Late_Blight',
            'keyakinan': "95.21%",
            'penanganan': 'Ini adalah penanganan dummy untuk Late Blight.',
            'rekomendasi_pestisida': 'Ini adalah pestisida dummy untuk Late Blight.',
            'info_lain': 'Pastikan server Anda berjalan dengan baik.'
        }
    ]
    # Pilih salah satu hasil secara acak
    return random.choice(dummy_results)

# --- Rute Flask untuk Webhook Telegram ---
@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def respond():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if not update.message:
        return 'ok'

    chat_id = update.message.chat.id
    
    # Cek apakah pesan berisi foto
    if update.message.photo:
        bot.send_message(chat_id=chat_id, text="🔍 Menerima foto, memproses dengan model dummy...")

        # Kita tidak perlu menyimpan foto, cukup panggil fungsi dummy
        result = dummy_predict_and_recommend("dummy_path.jpg")
        
        # Format pesan balasan
        reply_text = (
            f"✅ *Hasil Analisis (Dummy):*\n\n"
            f"*Penyakit Terdeteksi:* {result['penyakit_terdeteksi'].replace('_', ' ')}\n"
            f"*Tingkat Keyakinan:* {result['keyakinan']}\n\n"
            f"📝 *Saran Penanganan:*\n{result['penanganan']}\n\n"
            f"🧪 *Rekomendasi Pestisida:*\n{result['rekomendasi_pestisida']}\n\n"
            f"ℹ️ *Info Lain:*\n{result['info_lain']}"
        )
        
        # Kirim balasan ke pengguna
        bot.send_message(chat_id=chat_id, text=reply_text, parse_mode=telegram.ParseMode.MARKDOWN)

    else:
        # Balasan jika pengguna tidak mengirim foto
        reply_text = "Halo! Ini adalah mode testing. Silakan kirim foto daun tomat untuk mendapatkan balasan dummy."
        bot.send_message(chat_id=chat_id, text=reply_text)

    return 'ok'

# --- Rute untuk mengatur webhook ---
@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook(f'{APP_URL}/{TELEGRAM_BOT_TOKEN}')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

@app.route('/')
def index():
    return 'Aplikasi Bot Plantify (Mode Testing) Aktif!'
