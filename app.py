from flask import Flask, render_template, request, send_file
from stegano import lsb
from PIL import Image
import os
import wave

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# IMAGE EMBED
# =========================
@app.route("/embed", methods=["GET","POST"])
def embed():
    if request.method == "POST":
        file = request.files["image"]
        secret = request.form["secret"]

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        output = os.path.join(UPLOAD_FOLDER, "secret_image.png")

        secret_img = lsb.hide(path, secret)
        secret_img.save(output)

        return send_file(output, as_attachment=True)

    return render_template("embed.html")

# =========================
# IMAGE EXTRACT
# =========================
@app.route("/extract", methods=["GET","POST"])
def extract():
    if request.method == "POST":
        file = request.files["image"]

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        msg = lsb.reveal(path)

        return f"Yashirin xabar: {msg}"

    return render_template("extract.html")

# =========================
# AUDIO EMBED (WAV ONLY)
# =========================
@app.route("/audio_embed", methods=["GET","POST"])
def audio_embed():
    if request.method == "POST":
        file = request.files["audio"]
        secret = request.form["secret"]

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        song = wave.open(path, mode='rb')
        frame_bytes = bytearray(list(song.readframes(song.getnframes())))

        secret = secret + "###END###"
        bits = ''.join([format(ord(i), '08b') for i in secret])

        for i in range(len(bits)):
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
# AUDIO EXTRACT
# =========================
@app.route("/audio_extract", methods=["GET","POST"])
def audio_extract():
    if request.method == "POST":
        file = request.files["audio"]

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

        return f"Yashirin audio xabar: {hidden}"

    return render_template("audio_extract.html")

# =========================
# ERROR DEBUG
# =========================
@app.errorhandler(Exception)
def handle_error(e):
    return f"XATOLIK: {str(e)}"

# =========================
# RENDER PORT
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
