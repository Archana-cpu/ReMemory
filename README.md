# Rememory

ReMemory Chat Project Guide
Introduction

The ReMemory Chat project is a web application developed in Python with the Flask framework. It was designed to help people with Alzheimer's and dementia by facilitating the recall of their memories through conversational and multimedia interactions.

<span style="color: red;">Key features:</span>

Interactive chat: Communication with a chatbot based on an AI model (LLaMAChat) that answers the user's questions.
Image analysis: Processing uploaded images to generate a detailed description (via LLaVAAnalyzer).
Audio transcription: Converting audio files to text using the Whisper model.
Text-to-speech (TTS): Reading aloud the responses generated by the chatbot.
History management: Saving and summarizing conversations to keep a common thread and help with recall.
Tagging System: Automatic generation of relevant tags to enrich the metadata of uploaded images.

Project Structure

# File Description

AppHist.py: Flask application configuration, session management, chat, and uploads (images, audio).
data_preparer.py: Background process that merges user data, generates conversation summaries via AI, and updates JSON files.
main.py: Main logic of the chatbot and image analysis. Integrates audio transcription and speech synthesis.
tagging.py: Generates tagging prompts to analyze and extract tags from image comments and descriptions.
templates.py: Contains HTML templates (login, chat, image management, etc.) for the user interface.

# Features and Workflow

Login and Initialization
When a user logs in, the system:
Creates or loads their user record (JSON file).
Initializes the conversation history.
Asks questions to collect personal information (e.g. age, hobbies).

Chat and Interaction
The user can chat freely with the chatbot that:
Uses the last 20 messages to maintain context.
Answers questions and guides the user in the conversation.

Image Upload and Analysis
When an image is sent:
It is saved in a user-specific folder.
An analysis module (LLaVAAnalyzer) generates a detailed description of the image.
The history is updated with this information, and a tagging system can be applied to enrich the metadata.

Audio Transcription and Speech Synthesis
The user can send audio files that are transcribed into text.
The chatbot's answers can be read via speech synthesis, facilitating accessibility.

Conversation Management and Summarization
In the background, the data_preparer.py script:
Merges user data.
Generates detailed conversation summaries using an AI model.
Saves these summaries in the user record for easy recall.
