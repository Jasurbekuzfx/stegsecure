from flask import Flask, render_template, request, send_file
from PIL import Image
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# 🔐 TEXTNI BITLARGA O'TKAZISH
def text_to_bin(text):
    return ''.join(format(ord(i), '08b') for i in text)


# 🔓 BITLARNI TEXTGA QAYTARISH
def bin_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    text = ""
    for c in chars:
        if c == "11111111":  # END MARK
            break
        text += chr(int(c, 2))
    return text


@app.route("/")
def home():
    return render_template("index.html")


# 🧩 SECRETNI RASMGA YOZISH
@app.route("/embed", methods=["POST"])
def embed():
    file = request.files["image"]
    secret = request.form["secret"]

    filename = str(uuid.uuid4()) + ".png"
    path = os.path.join(UPLOAD_FOLDER, filename)

    img = Image.open(file).convert("RGB")
    pixels = list(img.getdata())

    binary_secret = text_to_bin(secret) + "11111111"
    data_index = 0

    new_pixels = []

    for pixel in pixels:
        r, g, b = pixel

        if data_index < len(binary_secret):
            r = (r & ~1) | int(binary_secret[data_index])
            data_index += 1

        if data_index < len(binary_secret):
            g = (g & ~1) | int(binary_secret[data_index])
            data_index += 1

        if data_index < len(binary_secret):
            b = (b & ~1) | int(binary_secret[data_index])
            data_index += 1

        new_pixels.append((r, g, b))

    img.putdata(new_pixels)
    img.save(path
@app.route("/embed_audio", methods=["POST"])
def embed_audio():
    file = request.files["audio"]
    secret = request.form["secret"]

    filename = str(uuid.uuid4()) + ".wav"
    path = os.path.join(UPLOAD_FOLDER, filename)

    audio_bytes = file.read()
    marker = b"STEGAUDIO:"

    new_audio = audio_bytes + marker + secret.encode()

    with open(path, "wb") as f:
        f.write(new_audio)

    return send_file(path, as_attachment=True)


@app.route("/extract_audio", methods=["POST"])
def extract_audio():
    file = request.files["audio"]

    audio_bytes = file.read()
    marker = b"STEGAUDIO:"

    if marker in audio_bytes:
        secret = audio_bytes.split(marker)[-1].decode(errors="ignore")
        return f"<h2>🔓 Secret: {secret}</h2>"

    return "<h2>❌ Secret topilmadi</h2>"
