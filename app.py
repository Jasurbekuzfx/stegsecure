from flask import Flask, render_template, request, send_file
from stegano import lsb
from PIL import Image
import os, wave, base64

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ======================
# SIMPLE ENCRYPT
# ======================
def encrypt(text, key):
    if key == "":
        return text
    return base64.b64encode((key+text).encode()).decode()

def decrypt(text, key):
    try:
        decoded = base64.b64decode(text).decode()
        if decoded.startswith(key):
            return decoded[len(key):]
    except:
        pass
    return "Parol noto‘g‘ri!"

# ======================
# HOME
# ======================
@app.route("/")
def home():
    return render_template("index.html")

# ======================
# IMAGE EMBED
# ======================
@app.route("/embed", methods=["POST"])
def embed():

    file = request.files.get("image")
    secret = request.form.get("secret","")
    password = request.form.get("password","")

    if not file:
        return "Rasm yuklanmadi"

    enc = encrypt(secret,password)

    path = os.path.join(UPLOAD_FOLDER,file.filename)
    file.save(path)

    output = os.path.join(UPLOAD_FOLDER,"secret.png")

    img = lsb.hide(path,enc)
    img.save(output)

    return send_file(output,as_attachment=True)

# ======================
# IMAGE EXTRACT
# ======================
@app.route("/extract", methods=["POST"])
def extract():

    file = request.files.get("image")
    password = request.form.get("password","")

    path = os.path.join(UPLOAD_FOLDER,file.filename)
    file.save(path)

    msg = lsb.reveal(path)

    return decrypt(msg,password)

# ======================
# AUDIO EMBED
# ======================
@app.route("/audio_embed", methods=["POST"])
def audio_embed():

    file = request.files.get("audio")
    secret = request.form.get("secret","")

    path = os.path.join(UPLOAD_FOLDER,file.filename)
    file.save(path)

    song = wave.open(path,mode='rb')
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))

    secret = secret+"###END###"
    bits = ''.join([format(ord(i),'08b') for i in secret])

    for i in range(len(bits)):
        frame_bytes[i] = (frame_bytes[i] & 254) | int(bits[i])

    output = os.path.join(UPLOAD_FOLDER,"secret_audio.wav")

    new_audio = wave.open(output,'wb')
    new_audio.setparams(song.getparams())
    new_audio.writeframes(bytes(frame_bytes))
    new_audio.close()
    song.close()

    return send_file(output,as_attachment=True)

# ======================
# AUDIO EXTRACT
# ======================
@app.route("/audio_extract", methods=["POST"])
def audio_extract():

    file = request.files.get("audio")

    path = os.path.join(UPLOAD_FOLDER,file.filename)
    file.save(path)

    song = wave.open(path,mode='rb')
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))

    extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
    chars=[]

    for i in range(0,len(extracted),8):
        byte = extracted[i:i+8]
        chars.append(chr(int(''.join(map(str,byte)),2)))

    message=''.join(chars)
    hidden = message.split("###END###")[0]

    return hidden

# ======================
# ERROR HANDLER
# ======================
@app.errorhandler(Exception)
def error(e):
    return f"XATOLIK: {str(e)}"

# ======================
# RENDER PORT
# ======================
if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
