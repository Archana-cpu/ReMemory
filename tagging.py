# tagging.py
import re
import os
import json

def generate_tagging_prompt(user_message, image_description=""):
    """Génère un prompt structuré pour le tagging"""
    return f"""Analysez le commentaire et la description d'image suivants pour générer des tags pertinents.
    Les tags doivent être courts, descriptifs et appartenir à l'une des catégories suivantes :
    - **animal** (ex: chat, chien, oiseau)
    - **personne** (ex: ami, famille, enfant)
    - **objet** (ex: voiture, téléphone, livre)
    - **lieu** (ex: plage, montagne, ville)
    - **activité** (ex: sport, voyage, cuisine)
    - **émotion** (ex: joie, tristesse, surprise)

    Format de réponse attendu : [catégorie1:valeur1, catégorie2:valeur2, ...]

    Exemples :
    1. Commentaire : "Voici mon chat Whiskers, il adore jouer dans le jardin."
    Description image : "Un chat noir et blanc dans un jardin ensoleillé."
    Tags : [animal:chat, lieu:jardin, émotion:joie]

    2. Commentaire : "Nous avons visité Paris cet été, c'était magnifique !"
    Description image : "La tour Eiffel avec un ciel bleu."
    Tags : [lieu:paris, monument:tour-eiffel, activité:voyage]

    3. Commentaire : "Mon nouveau téléphone est enfin arrivé !"
    Description image : "Un smartphone posé sur une table."
    Tags : [objet:téléphone, émotion:excitation]

    ---

    Commentaire : "{user_message}"
    Description image : "{image_description}"

    Tags : ["""

def save_user_info(username, user_info):
    """Saves user data to a JSON file."""
    user_info_path = f"users/{username}.json"
    with open(user_info_path, "w", encoding="utf-8") as f:
        json.dump(user_info, f, ensure_ascii=False, indent=4)

def extract_tags_from_response(llm_response):
    """Extrait les tags de la réponse LLM"""
    match = re.search(r'\[(.*?)\]', llm_response)
    if match:
        return [tag.strip().lower() for tag in match.group(1).split(',')]
    return []

def update_image_tags_Last(user_info, username, tags):
    """Met à jour les tags de la dernière image"""
    if "images" in user_info and user_info.get("images"):
        user_info["images"][-1]["tags"] = tags
        save_user_info(username, user_info)
        return {
            "role": "system",
            "content": f"Mise à jour des tags : {', '.join(tags)}"
        }
    return None

def update_image_tags(user_info, username, index, tags):
    """Met à jour les tags de l'image spécifiée par son index et sauvegarde les données."""
    if "images" in user_info and user_info.get("images") and index < len(user_info["images"]):
        user_info["images"][index]["tags"] = tags
        save_user_info(username, user_info)
        return {
            "role": "system",
            "content": f"Mise à jour des tags pour l'image {index} : {', '.join(tags)}"
        }
    return None

def handle_image_tagging(user_message, user_info, username, chatbot, index=None):
    """Gère le processus complet de tagging pour l'image spécifiée.
       Si index n'est pas fourni, on utilise la dernière image.
    """
    if "images" in user_info and user_info.get("images"):
        if index is None:
            index = len(user_info["images"]) - 1
        image = user_info["images"][index]
        image_description = image.get("description", "")
        # Si aucun message n'est fourni, on force un message par défaut
        if not user_message.strip():
            user_message = "Actualise les tags en fonction de la description."
        tagging_prompt = generate_tagging_prompt(user_message, image_description)
        tag_response = chatbot.ask(tagging_prompt)
        tags = extract_tags_from_response(tag_response)
        if tags:
            return update_image_tags(user_info, username, index, tags)
    return None

