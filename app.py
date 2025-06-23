import os
import tensorflow as tf
from tensorflow import keras
import numpy as np
from flask import Flask, request
import telegram

# --- Konfigurasi ---
# Token bot Anda dari BotFather (lebih aman disimpan sebagai environment variable)
TELEGRAM_BOT_TOKEN = 'GANTI_DENGAN_TOKEN_ANDA'
# Nama file model Anda
MODEL_FILE_PATH = 'plantify_disease_detection_model_final_production.keras'
# URL aplikasi Anda setelah di-deploy (misalnya, di Render)
APP_URL = 'https://nama-aplikasi-anda.onrender.com'

# --- Inisialisasi Aplikasi Flask dan Bot Telegram ---
app = Flask(__name__)
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# --- Muat Model CNN ---
# Lakukan ini sekali saat aplikasi dimulai agar tidak perlu memuat ulang setiap kali ada permintaan.
print("Memuat model CNN...")
model = tf.keras.models.load_model(MODEL_FILE_PATH)
print("Model berhasil dimuat.")

# --- Definisi Kelas dan Informasi Penyakit (Sama seperti di Poin 8) ---
CLASSES = ['Tomato_Bacterial_Spot', 'Tomato_Early_Blight', 'Tomato_Healthy', 'Tomato_Late_Blight', 'Tomato_Leaf_Mold', 'Tomato_Mosaic_Virus', 'Tomato_Septoria_Leaf_Spot', 'Tomato_Target_Spot', 'Tomato_Two_Spotted_Spider_Mite', 'Tomato_Yellow_Leaf_Curl_Virus']
IMG_WIDTH, IMG_HEIGHT = 224, 224

# Salin dictionary `disease_info_db` Anda yang lengkap ke sini
disease_info_db = {
    'Tomato_Healthy': {'penanganan': 'Tanaman sehat.', 'rekomendasi_pestisida': 'Tidak perlu.', 'info_lain': 'Lanjutkan perawatan rutin.'},
    # ... (isi semua kelas lainnya di sini) ...
}

# --- Fungsi Prediksi (Sama seperti di Poin 8) ---
def predict_and_recommend(image_path, model_to_use, class_names):
    try:
        img = tf.keras.preprocessing.image.load_img(image_path, target_size=(IMG_WIDTH, IMG_HEIGHT))
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_batch = np.expand_dims(img_array, axis=0)
        img_preprocessed = tf.keras.applications.mobilenet_v2.preprocess_input(img_batch)
    except Exception as e:
        return {'error': f"Gagal memproses gambar: {e}"}

    probs = model_to_use.predict(img_preprocessed)
    probs = tf.cast(probs, tf.float32)
    idx = np.argmax(probs[0])
    pred_class = class_names[idx]
    confidence = float(probs[0][idx]) * 100
    info = disease_info_db.get(pred_class, {})
    
    return {
        'penyakit_terdeteksi': pred_class,
        'keyakinan': f"{confidence:.2f}%",
        'penanganan': info.get('penanganan', 'Info tidak tersedia.'),
        'rekomendasi_pestisida': info.get('rekomendasi_pestisida', 'Info tidak tersedia.'),
        'info_lain': info.get('info_lain', 'Info tidak tersedia.')
    }

# --- Rute Flask untuk Webhook Telegram ---
@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def respond():
    # Ambil pembaruan dari Telegram
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    msg_id = update.message.message_id

    # Cek apakah pesan berisi foto
    if update.message.photo:
        # Kirim pesan bahwa foto sedang diproses
        bot.send_message(chat_id=chat_id, text="🔍 Foto Anda sedang dianalisis, harap tunggu...")

        # Ambil file foto dengan kualitas terbaik
        photo_id = update.message.photo[-1].file_id
        photo_file = bot.get_file(photo_id)
        
        # Simpan foto sementara
        file_path = f"{photo_id}.jpg"
        photo_file.download(file_path)

        # Lakukan prediksi
        try:
            result = predict_and_recommend(file_path, model, CLASSES)
            
            # Format pesan balasan
            if 'error' in result:
                reply_text = f"Terjadi kesalahan: {result['error']}"
            else:
                reply_text = (
                    f"✅ *Hasil Analisis:*\n\n"
                    f"*Penyakit Terdeteksi:* {result['penyakit_terdeteksi'].replace('_', ' ')}\n"
                    f"*Tingkat Keyakinan:* {result['keyakinan']}\n\n"
                    f"📝 *Saran Penanganan:*\n{result['penanganan']}\n\n"
                    f"🧪 *Rekomendasi Pestisida:*\n{result['rekomendasi_pestisida']}\n\n"
                    f"ℹ️ *Info Lain:*\n{result['info_lain']}"
                )
        except Exception as e:
            reply_text = f"Maaf, terjadi error internal saat menganalisis gambar: {e}"
        
        # Hapus file foto sementara
        os.remove(file_path)

        # Kirim balasan ke pengguna
        bot.send_message(chat_id=chat_id, text=reply_text, parse_mode=telegram.ParseMode.MARKDOWN)

    else:
        # Balasan jika pengguna tidak mengirim foto
        reply_text = "Halo! Silakan kirim foto daun tomat yang ingin Anda periksa."
        bot.send_message(chat_id=chat_id, text=reply_text)

    return 'ok'

# --- Rute untuk mengatur webhook ---
@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    # URL webhook harus menggunakan HTTPS
    s = bot.setWebhook(f'{APP_URL}/{TELEGRAM_BOT_TOKEN}')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

@app.route('/')
def index():
    return 'Aplikasi Bot Aktif!'

if __name__ == '__main__':
    # Jalankan aplikasi
    app.run(threaded=True)