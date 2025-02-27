#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fichier : main.py
Description : Application principale pour aider les personnes atteintes d’Alzheimer et de démence.
              Gère la conversation avec l’IA, l’historique des messages et la fiche utilisateur,
              et propose une analyse d'image via LLaVAAnalyzer.
              Lance automatiquement data_preparer.py en arrière-plan pour mettre à jour les données.
"""

import json
import os
import base64
import io
import pyttsx3         # Pour la synthèse vocale
import whisper         # Pour la transcription audio
from langdetect import detect  # Pour la détection de langue (facultatif)
from ollama import Client  # Client pour communiquer avec l'IA
from PIL import Image
import datetime
import threading
import subprocess
import sys

# Lancement de data_preparer.py en arrière-plan (approche ponctuelle, peu gourmande en ressources)
def start_data_preparer():
    try:
        subprocess.Popen([sys.executable, "data_preparer.py"])
        print("data_preparer.py a été lancé en arrière-plan.")
    except Exception as e:
        print("Erreur lors du lancement de data_preparer.py:", e)

#start_data_preparer()

# Chargement global du modèle Whisper pour éviter de le recharger à chaque appel
whisper_model = whisper.load_model("medium")

# Configuration du client Ollama
client = Client(host='http://127.0.0.1:11434')

# --- Classe LLaMAChat ---
class LLaMAChat:
    """
    Classe pour gérer les interactions avec l'IA via le client Ollama.
    Gère l'historique des conversations et la fiche utilisateur.
    Le paramètre 'save_history' (True par défaut) permet d'activer ou non l'enregistrement
    des messages dans l'historique.
    """
    def __init__(self, model_name='rolandroland/llama3.1-uncensored:latest', username="guest", save_history=True):
        self.model = model_name
        self.username = username
        self.save_history_flag = save_history
        self.history = self.load_history()
        self.saved_count = len(self.history)
        self.user_data = self.load_user_data()
        self.tts_engine = pyttsx3.init()

    def load_history(self) -> list:
        history_path = f"historique/{self.username}.json"  # Changement d'extension
        history = []
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    if isinstance(history, list):
                        return history
            except Exception as e:
                print(f"Erreur de lecture de l'historique : {e}")
        return []

    def save_history(self) -> None:
        os.makedirs("historique", exist_ok=True)
        history_path = f"historique/{self.username}.json"  # Changement d'extension
        # Sauvegarde de l'intégralité de l'historique à chaque fois
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=4)
        self.saved_count = len(self.history)

    def load_user_data(self) -> dict:
        user_info_path = f"users/{self.username}.json"
        if os.path.exists(user_info_path):
            with open(user_info_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "preferences" not in data:
                    data["preferences"] = {}
                return data
        return {"nom": self.username, "ton": "neutral", "language": "en", "preferences": {}}

    def ask(self, prompt: str) -> str:
        ia_name = "Angel"
        if not prompt.strip():
            return "Le prompt est vide. Veuillez fournir un message valide."
        if not any(msg.get("role") == "system" for msg in self.history):
            system_msg = {
                "role": "system",
                "content": (
                    f"User information: {json.dumps(self.user_data)}. "
                    f"Please respond as {ia_name}, a compassionate and supportive assistant dedicated to helping individuals with memory loss (such as dementia or Alzheimer’s) recall their cherished memories. "
                    "Your responses should be clear, concise, and secure, focusing solely on providing gentle assistance and practical guidance. "
                    "Avoid personalizing your identity or using language qui implique des liens familiaux ou des anecdotes personnelles."
                )
            }
            self.history.insert(0, system_msg)
        self.history.append({'role': 'user', 'content': prompt})
        if len(self.history) > 20:
            self.history = self.history[-20:]
        try:
            response = client.chat(model=self.model, messages=self.history)
            answer = response['message']['content']
        except Exception as e:
            answer = f"Error calling the AI: {str(e)}"
        self.history.append({'role': 'assistant', 'content': answer})
        if self.save_history_flag:
            self.save_history()
        return answer

    def generate_speech(self, text: str, rate: int = 80) -> None:
        if text:
            self.tts_engine.setProperty('rate', rate)
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()

# --- Classe LLaVAAnalyzer ---
class LLaVAAnalyzer:
    """
    Classe pour analyser une image et générer une description détaillée via l'IA.
    """
    def __init__(self, model_name='llava:7b'):
        self.model = model_name

    def describe_image(self, image_path: str) -> str:
        try:
            with Image.open(image_path) as img:
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            response = client.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': (
                        "Look at this image carefully and provide a detailed description in English, "
                        "mentioning objects, colors, emotions, and context."
                    ),
                    'images': [img_base64]
                }]
            )
            return response['message']['content']
        except Exception as e:
            return f"Error: {str(e)}"

def transcribe_audio(file_path: str) -> str:
    if not file_path or not os.path.exists(file_path):
         return "Error: audio file not found"
    try:
         result = whisper_model.transcribe(file_path, fp16=False)
         return result.get("text", "Error: transcription failed.")
    except Exception as e:
         return f"Error in transcription: {str(e)}"

def convert_history_to_messages(history: list) -> list:
    filtered_history = []
    for entry in history:
        if entry.get("role") in ["assistant", "user"]:
            filtered_history.append({
                "role": entry["role"],
                "content": entry["content"],
                "timestamp": datetime.datetime.now().isoformat()
            })
    return filtered_history

def save_conversation_history(username: str, history: list) -> list:
    directory = "historique"
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, f"{username}.json")
    filtered_history = convert_history_to_messages(history)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(filtered_history, f, ensure_ascii=False, indent=4)
    return filtered_history

def update_user_info_from_history(username: str, history: list) -> dict:
    user_info_path = f"users/{username}.json"
    if os.path.exists(user_info_path):
        with open(user_info_path, "r", encoding="utf-8") as f:
            user_info = json.load(f)
    else:
        user_info = {"nom": username, "preferences": {}}
    filtered_history = convert_history_to_messages(history)
    user_info["conversation_history"] = filtered_history
    with open(user_info_path, "w", encoding="utf-8") as f:
        json.dump(user_info, f, ensure_ascii=False, indent=4)
    return user_info

def warmup():
    try:
        dummy_history = [{"role": "system", "content": "Warming up chat model."}]
        _ = client.chat(model='rolandroland/llama3.1-uncensored:latest', messages=dummy_history)
        print("Warmup du modèle de chat terminé.")
    except Exception as e:
        print("Erreur lors du warmup du modèle de chat:", e)
    print("Warmup complet.")

warmup()

# # --- Menu interactif ---
# if __name__ == "__main__":
#     print("\n=== Application principale ===")
#     print("Choisissez une option :")
#     print("1 - Discuter avec l'IA")
#     print("2 - Analyser une image")
#     print("3 - Transcrire un fichier audio")
#     choix = input("Votre choix (1, 2 ou 3) : ").strip()
    
#     if choix == "1":
#         chat = LLaMAChat(username="guest")
#         user_input = input("Entrez votre message : ")
#         response = chat.ask(user_input)
#         print("Réponse de l'IA :", response)
#         if input("Voulez-vous entendre la réponse ? (o/n) : ").lower() == "o":
#             chat.generate_speech(response)
#     elif choix == "2":
#         image_path = input("Entrez le chemin de l'image à analyser : ").strip()
#         analyzer = LLaVAAnalyzer()
#         description = analyzer.describe_image(image_path)
#         print("Description de l'image :", description)
#     elif choix == "3":
#         audio_path = input("Entrez le chemin du fichier audio : ").strip()
#         transcription = transcribe_audio(audio_path)
#         print("Transcription :", transcription)
#     else:
#         print("Option non reconnue. Fin du programme.")