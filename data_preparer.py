#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fichier : data_preparer.py
Description :
  - Lit l’historique de conversation depuis historique/<Username>.json
    et la fiche utilisateur depuis users/<Username>.json (fusionne plusieurs fichiers s'ils existent).
  - Génère un résumé de la conversation actuelle via l’IA (format JSON strict).
  - Ajoute le nouveau résumé à la liste "conversation_resumer", afin de conserver tous les résumés.
  - Sauvegarde la fiche utilisateur mise à jour (ainsi qu’un fichier RAG).
  - IMPORTANT : L’historique n’est PAS supprimé afin de conserver toutes les informations.
  - Ce processus se répète toutes les 1 minute.
"""

import os
import json
import datetime
import time
from ollama import Client  # Client pour communiquer avec l'IA

# Configuration du client IA
client = Client(host='http://127.0.0.1:11434')


def merge_user_files(username: str) -> dict:
    user_dir = "users"
    merged = {
        "nom": username,
        "preferences": {},
        "images": [],
        "conversation_history": [],
        "conversation_resumer": []
    }
    files = sorted([f for f in os.listdir(user_dir)
                    if f.lower().startswith(username.lower()) and f.endswith(".json")])
    print(f"[DEBUG] Fichiers trouvés pour fusionner pour '{username}': {files}")
    for file in files:
        path = os.path.join(user_dir, file)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[DEBUG] Lecture réussie de {file}.")
            if "preferences" in data and isinstance(data["preferences"], dict):
                merged["preferences"].update(data["preferences"])
            if "images" in data and isinstance(data["images"], list):
                merged["images"].extend(data["images"])
            if "conversation_history" in data and isinstance(data["conversation_history"], list):
                merged["conversation_history"].extend(data["conversation_history"])
            if "conversation_resumer" in data and isinstance(data["conversation_resumer"], list):
                merged.setdefault("conversation_resumer", []).extend(data["conversation_resumer"])
        except Exception as e:
            print(f"[ERROR] Erreur lors de la lecture de {file}: {e}")
    return merged


class DataPreparer:
    def __init__(self, username: str):
        # Normalisation : première lettre en majuscule, le reste en minuscules
        self.username = username.capitalize()
        print(f"[DEBUG] Nom d'utilisateur normalisé: {self.username}")
        self.history_path = f"historique/{self.username}.json"
        self.user_info_path = f"users/{self.username}.json"
        self.rag_output_path = f"rag_data/{self.username}_rag.json"
        os.makedirs("rag_data", exist_ok=True)

    def load_history(self) -> list:
        if os.path.exists(self.history_path):
            print(f"[DEBUG] Fichier d'historique trouvé: {self.history_path}")
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    if isinstance(history, list):
                        print(f"[DEBUG] Historique chargé avec {len(history)} messages.")
                        return history
            except Exception as e:
                print(f"[ERROR] Erreur lors de la lecture de l'historique: {e}")
        else:
            print(f"[DEBUG] Aucun fichier d'historique trouvé pour {self.username}.")
        return []

    def load_user_info(self) -> dict:
        if os.path.exists(self.user_info_path):
            print(f"[DEBUG] Fichier utilisateur trouvé: {self.user_info_path}")
            try:
                with open(self.user_info_path, "r", encoding="utf-8") as f:
                    user_info = json.load(f)
                user_info.setdefault("preferences", {})
                user_info.setdefault("images", [])
                user_info.setdefault("conversation_history", [])
                user_info.setdefault("conversation_resumer", [])
                print("[DEBUG] Fiche utilisateur chargée.")
                return user_info
            except Exception as e:
                print(f"[ERROR] Erreur lors de la lecture de la fiche utilisateur: {e}")
        else:
            print(f"[DEBUG] Aucun fichier utilisateur trouvé pour {self.username}. Création d'une fiche par défaut.")
        return {"nom": self.username, "preferences": {}, "images": [],
                "conversation_history": [], "conversation_resumer": []}

    def prepare_prompt(self, history: list, user_info: dict) -> str:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        history_text = "\n".join([f"{msg['role']}: {msg['content']}"
                                  for msg in history if "role" in msg and "content" in msg])
        prompt = (
            f"Date actuelle : {current_date}\n\n"
            "Voici l'historique complet de notre conversation:\n"
            f"{history_text}\n\n"
            "Résume uniquement les informations importantes, telles que les événements marquants, les résultats obtenus, "
            "et les points clés qui pourraient aider à se remémorer la conversation. Veuillez conserver le maximum de détails importants. "
            "Ne répétez pas le texte original, mais reformulez-le de manière concise et pertinente. "
            "Le résumé doit être retourné sous forme d'une liste d'objets JSON, chaque objet ayant exactement deux clés : "
            "'role' et 'content'. Ne renvoyez aucun texte additionnel."
        )
        print("[DEBUG] Prompt généré pour résumé:")
        print(prompt)
        return prompt

    def call_ai_summarizer(self, prompt: str) -> list:
        try:
            print("[DEBUG] Envoi du prompt à l'IA pour résumé...")
            response = client.chat(
                model="rolandroland/llama3.1-uncensored:latest",
                messages=[{"role": "user", "content": prompt}]
            )
            summary_text = response['message']['content']
            print("[DEBUG] Réponse de l'IA reçue:")
            print(summary_text)
            try:
                summary = json.loads(summary_text)
                if isinstance(summary, list) and all(isinstance(item, dict) and "role" in item and "content" in item for item in summary):
                    return summary
                else:
                    print("[ERROR] Le résumé obtenu n'est pas au format attendu. Utilisation de la réponse brute.")
                    return [{"role": "summary", "content": summary_text}]
            except Exception as e:
                print(f"[ERROR] Erreur lors du parsing du résumé en JSON: {e}")
                return [{"role": "summary", "content": summary_text}]
        except Exception as e:
            print(f"[ERROR] Erreur lors de l'appel à l'IA pour résumer: {e}")
            return []

    def save_user_info(self, user_info: dict) -> None:
        with open(self.user_info_path, "w", encoding="utf-8") as f:
            json.dump(user_info, f, ensure_ascii=False, indent=4)
        print(f"[DEBUG] Fiche utilisateur mise à jour dans {self.user_info_path}")

    def save_rag_data(self, data: dict) -> None:
        with open(self.rag_output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[DEBUG] Données préparées sauvegardées dans {self.rag_output_path}")

    # La suppression de l'historique est désactivée pour conserver toutes les informations
    # def clear_history(self) -> None:
    #     with open(self.history_path, "w", encoding="utf-8") as f:
    #         json.dump([], f)
    #     print(f"[DEBUG] L'historique {self.history_path} a été vidé.")

    def update_conversation_history_summary(self, user_info: dict, history: list) -> dict:
        prompt = self.prepare_prompt(history, user_info)
        summary_list = self.call_ai_summarizer(prompt)
        new_summary_text = " ".join([item["content"] for item in summary_list if "content" in item]).strip()
        if not new_summary_text:
            print("[DEBUG] Aucun nouveau résumé généré pour cette session.")
            return user_info

        # Ajoute le nouveau résumé dans la clé "conversation_resumer" sans supprimer les précédents
        if "conversation_resumer" not in user_info or not isinstance(user_info["conversation_resumer"], list):
            user_info["conversation_resumer"] = []
        user_info["conversation_resumer"].append({"resumer": new_summary_text})
        self.save_user_info(user_info)
        print("[DEBUG] Nouveau résumé ajouté dans 'conversation_resumer' de la fiche utilisateur.")
        return user_info

    def run_preparation(self) -> None:
        while True:
            print("\n=== Début de la mise à jour ===")
            history = self.load_history()
            if not history:
                print("[DEBUG] L'historique est vide, aucune mise à jour effectuée.")
                time.sleep(60)
                continue
            user_info = self.load_user_info()
            print(f"[DEBUG] Historique lu: {len(history)} messages.")
            prompt = self.prepare_prompt(history, user_info)
            summary_result = self.call_ai_summarizer(prompt)
            if summary_result:
                print("[DEBUG] Résumé obtenu avec succès.")
                user_info = self.update_conversation_history_summary(user_info, history)
                self.save_rag_data(user_info)
            else:
                print("[ERROR] Échec de la mise à jour via l'IA.")
            # Ne pas vider l'historique pour conserver toutes les informations
            print("=== Mise à jour terminée. Attente d'une minute avant la prochaine exécution... ===")
            time.sleep(180)


if __name__ == "__main__":
    import sys
    user_dir = "users"
    username = None
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        if os.path.exists(user_dir):
            files = sorted([f for f in os.listdir(user_dir) if f.endswith(".json")])
            if files:
                username = files[0].rsplit(".", 1)[0]
                print(f"[DEBUG] Fichier utilisateur détecté automatiquement : {files[0]}")
    if not username:
        username = "guest"
    username = username.capitalize()
    print(f"[DEBUG] Utilisateur détecté : {username}")
    if os.path.exists(user_dir):
        user_files = [f for f in os.listdir(user_dir)
                      if f.lower().startswith(username.lower()) and f.endswith(".json")]
        if len(user_files) > 1:
            print(f"[DEBUG] Plusieurs fichiers trouvés pour '{username}'. Fusion en cours...")
            merged_data = merge_user_files(username)
            merged_file_path = os.path.join(user_dir, f"{username}.json")
            with open(merged_file_path, "w", encoding="utf-8") as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=4)
            print(f"[DEBUG] Fichier fusionné sauvegardé sous {merged_file_path}")
    preparer = DataPreparer(username)
    preparer.run_preparation()
