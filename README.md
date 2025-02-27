# Rememory

Guide du Projet ReMemory Chat
Introduction

Le projet ReMemory Chat est une application web développée en Python avec le framework Flask. Il a été conçu pour aider les personnes atteintes d’Alzheimer et de démence en facilitant la remémoration de leurs souvenirs à travers des interactions conversationnelles et multimédias.

<span style="color: red;">Fonctionnalités clés :</span>

    Chat interactif : Communication avec un chatbot basé sur un modèle IA (LLaMAChat) qui répond aux questions de l’utilisateur.
    Analyse d’images : Traitement des images uploadées pour générer une description détaillée (via LLaVAAnalyzer).
    Transcription audio : Conversion des fichiers audio en texte grâce au modèle Whisper.
    Synthèse vocale (TTS) : Lecture à voix haute des réponses générées par le chatbot.
    Gestion de l’historique : Sauvegarde et résumé des conversations pour conserver un fil conducteur et aider à la remémoration.
    Système de tagging : Génération automatique de tags pertinents pour enrichir les métadonnées des images uploadées.

Structure du Projet

# Fichier Description

AppHist.py : Configuration de l’application Flask, gestion des sessions, du chat, et des uploads (images, audio).
data_preparer.py : Processus en arrière-plan qui fusionne les données utilisateur, génère des résumés de conversation via l’IA, et met à jour les fichiers JSON.
main.py : Logique principale du chatbot et de l’analyse d’image. Intègre la transcription audio et la synthèse vocale.
tagging.py : Génère des prompts de tagging pour analyser et extraire des tags à partir des commentaires et descriptions d’images.
templates.py : Contient les templates HTML (login, chat, gestion des images, etc.) pour l’interface utilisateur.

# Fonctionnalités et Workflow

    Connexion et Initialisation
    Lorsqu’un utilisateur se connecte, le système :
        Crée ou charge sa fiche utilisateur (fichier JSON).
        Initialise l’historique de conversation.
        Pose des questions pour recueillir des informations personnelles (ex. âge, hobbies).

    Chat et Interaction
    L’utilisateur peut discuter librement avec le chatbot qui :
        Utilise les 20 derniers messages pour maintenir le contexte.
        Répond aux questions et guide l’utilisateur dans la conversation.

    Upload et Analyse d’Image
    Lorsqu’une image est envoyée :
        Elle est sauvegardée dans un dossier spécifique à l’utilisateur.
        Un module d’analyse (LLaVAAnalyzer) génère une description détaillée de l’image.
        L’historique est mis à jour avec ces informations, et un système de tagging peut être appliqué pour enrichir les métadonnées.

    Transcription Audio et Synthèse Vocale
    L’utilisateur peut envoyer des fichiers audio qui sont transcrits en texte.
    Les réponses du chatbot peuvent être lues via une synthèse vocale, facilitant l’accessibilité.

    Gestion et Résumé de la Conversation
    En arrière-plan, le script data_preparer.py :
        Fusionne les données de l’utilisateur.
        Génère des résumés détaillés de la conversation grâce à un modèle IA.
        Sauvegarde ces résumés dans la fiche utilisateur pour faciliter la remémoration.
