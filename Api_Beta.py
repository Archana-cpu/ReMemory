from flask import Flask, request, jsonify
from main_testFinal import LLaMAChat, transcribe_audio, LLaVAAnalyzer
import os
app = Flask(__name__)

# Route pour envoyer un message à l'IA
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    username = data.get("username", "guest")
    message = data.get("message", "")
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    chatbot = LLaMAChat(username=username)
    response = chatbot.ask(message)
    return jsonify({"response": response})

# Route pour la transcription audio
@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400
    
    audio_file = request.files["audio"]
    file_path = os.path.join("uploads", audio_file.filename)
    os.makedirs("uploads", exist_ok=True)
    audio_file.save(file_path)
    
    transcript = transcribe_audio(file_path)
    return jsonify({"transcript": transcript})

# Route pour analyser une image
@app.route("/describe", methods=["POST"])
def describe():
    if "image" not in request.files:
        return jsonify({"error": "No image file uploaded"}), 400
    
    image_file = request.files["image"]
    file_path = os.path.join("uploads", image_file.filename)
    os.makedirs("uploads", exist_ok=True)
    image_file.save(file_path)
    
    analyzer = LLaVAAnalyzer()
    description = analyzer.describe_image(file_path)
    return jsonify({"description": description})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
