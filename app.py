from flask import Flask, render_template, request, send_file
from stegano import lsb
from PIL import Image
from cryptography.fernet import Fernet
import os
import wave
import base64
import hashlib

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# 🔐 PASSWORD → AES KEY
# =========================
def make_key(password):
    key = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key)

def encrypt(text, password):
    f = Fernet(make_key(password))
    return f.encrypt(text.encode()).decode()

def decrypt(text, password):
    f = Fernet(make_key(password))
    return f.decrypt(text.encode()).decode()

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# 🖼 IMAGE EMBED
# =========================
@app.route("/embed", methods=["GET","POST"])
def embed():
    if request.method == "POST":
        file = request.files["image"]
        secret = request.form["secret"]
        password = request.form["password"]

        enc = encrypt(secret, password)

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        output = os.path.join(UPLOAD_FOLDER, "secret_image.png")

        img = lsb.hide(path, enc)
        img.save(output)

        return send_file(output, as_attachment=True)

    return render_template("embed.html")

# =========================
# 🖼 IMAGE EXTRACT
# =========================
@app.route("/extract", methods=["GET","POST"])
def extract():
    if request.method == "POST":
        file = request.files["image"]
        password = request.form["password"]

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        hidden = lsb.reveal(path)

        if hidden:
            try:
                msg = decrypt(hidden, password)
            except:
                msg = "❌ Parol noto‘g‘ri"

            return f"Yashirin xabar: {msg}"

        return "Xabar topilmadi"

    return render_template("extract.html")

# =========================
# 🔊 AUDIO EMBED (WAV)
# =========================
@app.route("/audio_embed", methods=["GET","POST"])
def audio_embed():
    if request.method == "POST":
        file = request.files["audio"]
        secret = request.form["secret"]
        password = request.form["password"]

        enc = encrypt(secret, password) + "###END###"

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        song = wave.open(path, mode='rb')
        frame_bytes = bytearray(list(song.readframes(song.getnframes())))

        bits = ''.join([format(ord(i), '08b') for i in enc])

        for i in range(len(bits)):
            if i < len(frame_bytes):
                frame_bytes[i] = (frame_bytes[i] & 254) | int(bits[i])

        output = os.path.join(UPLOAD_FOLDER, "secret_audio.wav")

        new_audio = wave.open(output, 'wb')
        new_audio.setparams(song.getparams())
        new_audio.writeframes(bytes(frame_bytes))
        new_audio.close()
        song.close()

        return send_file(output, as_attachment=True)

    return render_template("audio_embed.html")

# =========================
# 🔊 AUDIO EXTRACT
# =========================
@app.route("/audio_extract", methods=["GET","POST"])
def audio_extract():
    if request.method == "POST":
        file = request.files["audio"]
        password = request.form["password"]

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        song = wave.open(path, mode='rb')
        frame_bytes = bytearray(list(song.readframes(song.getnframes())))

        extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
        chars = []

        for i in range(0, len(extracted), 8):
            byte = extracted[i:i+8]
            chars.append(chr(int(''.join(map(str, byte)), 2)))

        message = ''.join(chars)
        hidden = message.split("###END###")[0]

        try:
            msg = decrypt(hidden, password)
        except:
            msg = "❌ Parol noto‘g‘ri"

        return f"Yashirin audio xabar: {msg}"

    return render_template("audio_extract.html")

# =========================
# ERROR HANDLER (PRO)
# =========================
@app.errorhandler(Exception)
def error(e):
    return f"🚨 SERVER XATOLIK: {str(e)}"

# =========================
# RENDER SERVER
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
