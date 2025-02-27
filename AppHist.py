from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from flask_session import Session
import os, json, threading, uuid, subprocess
import jinja2
from main import *  # Importation des modules personnalisés (chat, analyse d'image, etc.)
from gtts import gTTS
import pyttsx3
from tagging import handle_image_tagging
from PIL import Image
import sys
import textwrap
from templates import templates
from langdetect import detect, DetectorFactory


# Pour garantir la reproductibilité des résultats de détection
DetectorFactory.seed = 0


app = Flask(__name__)
app.secret_key = 'votre_clé_secrète'
app.jinja_loader = jinja2.DictLoader(templates)

# Configuration de Flask-Session pour stocker la session côté serveur (système de fichiers)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(app.root_path, "flask_session")
app.config["SESSION_PERMANENT"] = False
Session(app)

# IMPORTANT : Pour TTS, nous utilisons subprocess afin d'éviter les conflits avec la boucle d'événements
def generate_speech(text):
    """Génère la synthèse vocale en détectant la langue du texte de façon robuste."""
    if not text.strip():
        return
    try:
        # Détection de la langue avec langdetect
        lang = detect(text)
        if lang not in ['fr', 'en']:
            lang = 'en'
        tts = gTTS(text=text, lang=lang)
        # Sauvegarde dans un fichier temporaire
        tmp_filename = f"temp_tts_{uuid.uuid4().hex}.mp3"
        tts.save(tmp_filename)
        
        # Lecture du fichier audio selon le système d'exploitation
        if os.name == "nt":  # Pour Windows
            os.startfile(tmp_filename)
        else:
            subprocess.Popen(["mpg123", tmp_filename])
    except Exception as e:
        print(f"[ERROR] Erreur lors de la génération du TTS : {e}")

def stop_tts_func():
    # Ici, stop_tts ne peut pas interrompre le subprocess lancé.
    return "TTS arrêté (le processus se termine normalement)"

# Liste des questions pour collecter les informations utilisateur
questions_base = [
    "What is your age?",
    "What are your hobbies?",
    "Which city do you live in?",
    "Do you have any pets?",
    "What is your favorite dish?",
    "What is your favorite movie or TV series?",
    "What is your favorite music style?",
    "What is your dream or goal in life?"
]

def get_user_info(username):
    """Récupère ou crée le fichier JSON de l'utilisateur avec la structure de base."""
    user_info_path = f"users/{username}.json"
    defaults = {
        "nom": username,
        "preferences": {},
        "conversation_history": [],
        "images": [],
        "conversation_resumer": []
    }
    if os.path.exists(user_info_path):
        with open(user_info_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in defaults:
            if key not in data:
                data[key] = defaults[key]
        if not data.get("preferences"):
            return data, True
        return data, False
    else:
        os.makedirs("users", exist_ok=True)
        with open(user_info_path, "w", encoding="utf-8") as f:
            json.dump(defaults, f, ensure_ascii=False, indent=4)
        return defaults, True

def save_user_info(username, user_info):
    """Sauvegarde la fiche utilisateur en respectant la structure de base."""
    user_info_path = f"users/{username}.json"
    with open(user_info_path, "w", encoding="utf-8") as f:
        json.dump(user_info, f, ensure_ascii=False, indent=4)

def get_next_question(user_info):
    """Renvoie la prochaine question non renseignée."""
    for question in questions_base:
        if question not in user_info.get("preferences", {}):
            return question
    return None

def convert_history_to_messages(history: list) -> list:
    """
    Filtre l’historique pour afficher uniquement les messages (assistant, user et system_question).
    Les messages "system_question" seront affichés avec l'avatar de l'assistant.
    """
    filtered = []
    for entry in history:
        role = entry.get("role")
        content = entry.get("content")
        if role in ["assistant", "user", "system_question"]:
            filtered.append({"role": "assistant" if role=="system_question" else role, "content": content})
    return filtered

def save_conversation_history(username: str, history: list) -> list:
    """
    Charge l'historique existant depuis 'historique/<username>.json', y ajoute les nouveaux messages,
    et sauvegarde l'historique cumulatif.
    """
    directory = "historique"
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, f"{username}.json")
    existing_history = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing_history = json.load(f)
        except Exception as e:
            print(f"[ERROR] Erreur lors du chargement de l'historique existant : {e}")
    combined = existing_history + convert_history_to_messages(history)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=4)
    return combined

def update_user_info_from_history(username: str, history: list) -> dict:
    """Met à jour la clé 'conversation_history' dans la fiche utilisateur."""
    user_info, _ = get_user_info(username)
    filtered_history = convert_history_to_messages(history)
    user_info["conversation_history"] = filtered_history
    save_user_info(username, user_info)
    return user_info

def update_uploaded_cards(username):
    user_info, _ = get_user_info(username)
    return user_info.get("images", [])

def play_card_description(index, username):
    user_info, _ = get_user_info(username)
    images = user_info.get("images", [])
    if index < len(images):
        description = images[index].get("description", "")
        generate_speech(description)
        return "Lecture lancée"
    return "Aucune description disponible"

def chat_response(user_message, history, username, tts_enabled):
    """
    Gère la réponse de l'utilisateur.
      - En mode image, ajoute le message à la description de l'image en cours.
      - En mode collecte de préférences, enregistre la réponse et insère la prochaine question.
      - Sinon, envoie la requête au chatbot (seuls les 20 derniers messages sont utilisés).
    """
    if session.get("image_mode", False):
        current_index = session.get("current_image_index", None)
        if current_index is not None:
            user_info, _ = get_user_info(username)
            images = user_info.get("images", [])
            if current_index < len(images):
                images[current_index]["description"] += " " + user_message
                save_user_info(username, user_info)
                tag_update = handle_image_tagging(user_message, user_info, username, LLaMAChat(username=username))
                if tag_update:
                    history.append({"role": "assistant", "content": tag_update["content"]})
                history.append({"role": "assistant", "content": f"(Message ajouté à l'image) {user_message}"})
                save_conversation_history(username, history)
                update_user_info_from_history(username, history)
                return history

    user_info, _ = get_user_info(username)
    if "current_question" in user_info:
        current_q = user_info["current_question"]
        user_info["preferences"][current_q] = user_message
        user_info.pop("current_question")
        save_user_info(username, user_info)
        next_q = get_next_question(user_info)
        if next_q:
            user_info["current_question"] = next_q
            save_user_info(username, user_info)
            history.append({"role": "system_question", "content": next_q})
            save_conversation_history(username, history)
            update_user_info_from_history(username, history)
            return history
        else:
            history.append({"role": "assistant", "content": "Merci pour vos réponses. Vous pouvez maintenant discuter librement."})
            save_conversation_history(username, history)
            update_user_info_from_history(username, history)
            return history
    else:
        truncated_history = history[-20:] if len(history) > 20 else history
        for msg in truncated_history:
            if msg.get("role") == "system_question":
                msg["role"] = "assistant"
        chatbot = LLaMAChat(username=username)
        chatbot.history = truncated_history
        response = chatbot.ask(user_message)
        history = chatbot.history

    if tts_enabled and response.strip():
        generate_speech(response)
    save_conversation_history(username, history)
    update_user_info_from_history(username, history)
    return history

def image_response(image_obj, history, username):
    """
    Traite l'envoi d'une image :
      - Sauvegarde l'image dans le dossier images/<username>.
      - Analyse son contenu pour générer une description.
      - Ajoute les métadonnées de l'image dans la fiche utilisateur.
    """
    if image_obj is None:
        return history
    user_info, _ = get_user_info(username)
    user_dir = os.path.join("images", username)
    os.makedirs(user_dir, exist_ok=True)
    # Utiliser un nom de fichier basé sur le nombre d'images déjà enregistrées dans la fiche utilisateur
    image_filename = f"{len(user_info.get('images', [])) + 1}.jpg"
    image_path = os.path.join(user_dir, image_filename).replace("\\", "/")
    image_obj.save(image_path)
    analyzer = LLaVAAnalyzer()
    description = analyzer.describe_image(image_path)
    history.append({"role": "assistant", "content": f"**Image Description**: {description}"})
    if "images" not in user_info:
        user_info["images"] = []
    image_metadata = {
         "filename": image_filename,
         "path": image_path,
         "description": description,
         "tags": []
    }
    user_info["images"].append(image_metadata)
    save_user_info(username, user_info)
    save_conversation_history(username, history)
    update_user_info_from_history(username, history)
    generate_speech(description)
    # Active le mode image
    session["image_mode"] = True
    session["current_image_index"] = len(user_info["images"]) - 1
    return history

@app.route("/", methods=["GET", "POST"])
def login():
    """
    Route de connexion.
      - Si l'utilisateur est nouveau ou ses préférences sont vides, la première question est assignée.
      - Sinon, l'historique existant est chargé.
      -> On ne réinitialise pas les indicateurs de mode image s'ils existent déjà en session.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            flash("Veuillez entrer un nom d'utilisateur.")
            return redirect(url_for("login"))
        session["username"] = username
        user_info, is_new = get_user_info(username)
        if is_new or not user_info.get("preferences"):
            first_q = get_next_question(user_info)
            if first_q:
                user_info["current_question"] = first_q
                save_user_info(username, user_info)
        else:
            history_file = f"historique/{username}.json"
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    session["chat_history"] = json.load(f)
            else:
                session["chat_history"] = []
        session.setdefault("chat_history", [])
        session.setdefault("image_mode", False)
        session.setdefault("current_image_index", None)
        subprocess.Popen([sys.executable, "data_preparer.py", username])
        print(f"[DEBUG] Utilisateur détecté : {username}")
        return redirect(url_for("chat"))
    return render_template("login.html", title="Login - ReMemory Chat")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    """
    Route de chat :
      - Charge l'historique depuis le fichier.
      - Ajoute la question en attente si présente.
      - Traite les messages envoyés (via JSON ou formulaire).
    """
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    history = []
    history_file = f"historique/{username}.json"
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
    user_info, _ = get_user_info(username)
    if "current_question" in user_info and user_info["current_question"]:
        system_msg = {"role": "system_question", "content": user_info["current_question"]}
        if not history or (history and history[0].get("role") != "system_question"):
            history.insert(0, system_msg)
        else:
            history[0]["content"] = user_info["current_question"]
    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            user_message = data.get("message", "")
            tts_enabled = data.get("tts", False)
            updated_history = chat_response(user_message, history, username, tts_enabled)
            last_reply = ""
            for msg in reversed(updated_history):
                if msg["role"] in ("assistant", "system_question"):
                    last_reply = msg["content"]
                    break
            return jsonify({"reply": last_reply})
        else:
            user_message = request.form.get("message", "")
            tts_enabled = request.form.get("tts") == "on"
            updated_history = chat_response(user_message, history, username, tts_enabled)
            return redirect(url_for("chat"))
    return render_template("chat.html",
                           title="Chat - ReMemory Chat",
                           username=username,
                           chat_history=[])#convert_history_to_messages(history) a la place tu tableau vide si on veut afficher hitorique dan sle chat

@app.route("/upload_image", methods=["POST"])
def upload_image():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    history = []
    history_file = f"historique/{username}.json"
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
    if "image" in request.files:
        image_file = request.files["image"]
        try:
            image_obj = Image.open(image_file.stream)
            history = image_response(image_obj, history, username)
        except Exception as e:
            flash("Erreur lors du traitement de l'image.")
    save_conversation_history(username, history)
    return redirect(url_for("chat"))

@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    history = []
    history_file = f"historique/{username}.json"
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
    if "audio" in request.files:
        audio_file = request.files["audio"]
        try:
            audio_dir = "audio"
            os.makedirs(audio_dir, exist_ok=True)
            filename = f"recorded_{uuid.uuid4().hex}.webm"
            filepath = os.path.join(audio_dir, filename)
            audio_file.save(filepath)
            text = transcribe_audio(filepath)
            history = chat_response(text, history, username, tts_enabled=True)
        except Exception as e:
            flash("Erreur lors du traitement de l'audio: " + str(e))
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    save_conversation_history(username, history)
    return redirect(url_for("chat"))

@app.route("/clear_image")
def clear_image():
    session["image_mode"] = False
    session["current_image_index"] = None
    flash("Le mode image est désactivé. Le chat est revenu en mode normal.")
    return redirect(url_for("chat"))

@app.route("/images")
def images():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    cards = update_uploaded_cards(username)
    return render_template("images.html", title="Images Uploadées - ReMemory Chat", username=username, cards=cards)

@app.route("/edit_image/<int:index>", methods=["GET", "POST"])
def edit_image(index):
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    user_info, _ = get_user_info(username)
    images = user_info.get("images", [])
    if index >= len(images):
        flash("Image non trouvée.")
        return redirect(url_for("images"))
    if request.method == "POST":
        new_description = request.form.get("description", "")
        new_tags = request.form.get("tags", "")
        tags_list = [tag.strip() for tag in new_tags.split(",") if tag.strip()]
        images[index]["description"] = new_description
        images[index]["tags"] = tags_list
        save_user_info(username, user_info)
        flash("Image modifiée avec succès.")
        return redirect(url_for("images"))
    image = images[index]
    return render_template("edit_image.html", title="Modifier l'image", username=username, index=index, image=image)

@app.route("/delete_image/<int:index>")
def delete_image(index):
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    user_info, _ = get_user_info(username)
    images = user_info.get("images", [])
    if index >= len(images):
        flash("Image non trouvée.")
    else:
        image = images.pop(index)
        if os.path.exists(image["path"]):
            os.remove(image["path"])
        save_user_info(username, user_info)
        flash("Image supprimée.")
    return redirect(url_for("images"))

@app.route("/update_tags/<int:index>")
def update_tags(index):
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    user_info, _ = get_user_info(username)
    images = user_info.get("images", [])
    if index < len(images):
        from tagging import handle_image_tagging
        result = handle_image_tagging("", user_info, username, LLaMAChat(username=username), index)
        if result:
            flash(result["content"])
        else:
            flash("Aucun tag généré ou erreur lors de la mise à jour.")
    else:
        flash("Image non trouvée.")
    return redirect(url_for("images"))

@app.route("/play_description/<int:index>")
def play_description(index):
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    message = play_card_description(index, username)
    flash(message)
    return redirect(url_for("images"))

@app.route("/stop_tts")
def stop_tts():
    message = stop_tts_func()
    flash(message)
    return redirect(url_for("images"))

@app.route("/logout")
def logout_route():
    session.clear()
    return redirect(url_for("login"))

@app.route("/serve_image/<path:filename>")
def serve_image(filename):
    return send_from_directory("images", filename)

@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory("audio", filename)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
