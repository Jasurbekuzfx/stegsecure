from flask import Flask, render_template, request, send_file
import subprocess, os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/embed", methods=["POST"])
def embed():
    image = request.files["image"]
    secret = request.form["secret"]
    password = request.form["password"]

    img_path = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(img_path)

    secret_file = os.path.join(UPLOAD_FOLDER,"secret.txt")
    with open(secret_file,"w") as f:
        f.write(secret)

    subprocess.run([
        "steghide.exe","embed",
        "-cf",img_path,
        "-ef",secret_file,
        "-p",password,
        "-f"
    ])

    return send_file(img_path,as_attachment=True)

@app.route("/extract", methods=["POST"])
def extract():
    image = request.files["image"]
    password = request.form["password"]

    img_path = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(img_path)

    secret_file = os.path.join(UPLOAD_FOLDER,"secret.txt")

    subprocess.run([
        "steghide.exe","extract",
        "-sf",img_path,
        "-p",password,
        "-xf",secret_file,
        "-f"
    ])

    if os.path.exists(secret_file):
        return send_file(secret_file,as_attachment=True)

    return "Secret topilmadi"

    if os.path.exists("secret.txt"):
        return send_file("secret.txt",as_attachment=True)

    return "Secret topilmadi"

import os

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


