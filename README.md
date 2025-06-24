# 🚨SARAI
SARAI (Smart Assistive Response AI) is an AI-powered emergency call handling system that automates the process of receiving, analyzing, and prioritizing distress calls. It uses speech-to-text transcription, natural language processing (NLP), and keyword-based emergency grading to assess urgency in real time. 

# 🧠 Core Technologies
Flask: Web framework to serve API endpoints and manage request flow.

Twilio Voice: Receives incoming emergency calls and records user responses.

AssemblyAI: Transcribes recorded voice messages into text.

OpenAI GPT: Analyzes transcribed text to extract emergency details like name, location, type, and urgency.

MySQL (via XAMPP): Stores structured emergency call records.

Web3.py + Ethereum: Logs operations on a smart contract for traceability (optional).

ngrok: Exposes the local Flask app for external access.

# 🛠 Features
Accept emergency voice calls via Twilio

AI-powered speech transcription and emergency classification

Store structured call data (name, location, type, priority, status)

View real-time emergency statistics and recent call history

REST API endpoints for dashboard integration

Optional smart contract logging for secure audit trail

Easy ngrok setup for local development with public accessibility
