from flask import Flask, request, render_template, jsonify
import requests
from pyngrok import ngrok
import time
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from threading import Thread
from gpt import send_req
from datetime import datetime
import json
from sendSMS import sendMSG
from web3 import Web3
from env import getPrivateKey
import random
import mysql.connector
from mysql.connector import Error
import os
import subprocess
import time
import requests


app = Flask(__name__)
base_url = "https://api.assemblyai.com/v2"

# Twilio Client
client = Client("ACcd9f88833ecd42eaa34bd32dxa8c61097", "e15061e6780ad9581xe94ad04f24dc9e6")

# Ethereum setup
provider = Web3.HTTPProvider('https://eth-sepolia.g.alchemy.com/v2/4aOT7ezZZe-7UVJ9UGEcHYtHWnd1O154j')
w3 = Web3(provider)
contract_address = Web3.to_checksum_address("0xe7f1725E77334CE288F8367e1Bb143E90bb3F0512")


contract_abi = [
    # ABI content unchanged
    {
      "inputs": [],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "id",
          "type": "uint256"
        },
        {
          "internalType": "string",
          "name": "D",
          "type": "string"
        }
      ],
      "name": "addOperation",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "op",
          "type": "address"
        }
      ],
      "name": "addToWhitelist",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "getOperations",
      "outputs": [
        {
          "components": [
            {
              "internalType": "uint256",
              "name": "id",
              "type": "uint256"
            },
            {
              "internalType": "string",
              "name": "data",
              "type": "string"
            },
            {
              "internalType": "uint256",
              "name": "status",
              "type": "uint256"
            }
          ],
          "internalType": "struct Contract.OperationData[]",
          "name": "",
          "type": "tuple[]"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "op",
          "type": "address"
        }
      ],
      "name": "removeFromWhitelist",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "id",
          "type": "uint256"
        },
        {
          "internalType": "uint256",
          "name": "s",
          "type": "uint256"
        }
      ],
      "name": "setStatus",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    }
]

contract = w3.eth.contract(address=contract_address, abi=contract_abi)
sender_address = Web3.to_checksum_address("0x8453ada3A9E671E0f115B2f2A2939b03aD519615")
w3.eth.defaultAccount = sender_address
# Database setup
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'mysql'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Error as e:
        print(f"Database connection failed: {e}")
        raise

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/api/system/status')
def system_status():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM emergency_calls WHERE status = 'active'")
        active_calls = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM emergency_calls WHERE DATE(time) = CURDATE()")
        recent_calls = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return jsonify({
            "status": "operational",
            "active_calls": active_calls,
            "recent_calls": recent_calls
        })
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "error": str(e)
        }), 500

@app.route('/api/calls/recent')
def get_recent_calls():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM emergency_calls ORDER BY time DESC LIMIT 10")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "calls": rows})
  
@app.route('/api/calls/<int:call_id>')
def get_call(call_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM emergency_calls WHERE id = %s", (call_id,))
    call = cursor.fetchone()
    cursor.close()
    conn.close()
    if call:
        return jsonify({"status": "success", "call": call})
    else:
        return jsonify({"status": "error", "message": "Call not found"}), 404

@app.route('/api/calls/<int:call_id>/resolve', methods=['POST'])
def resolve_call(call_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE emergency_calls SET status = 'resolved' WHERE id = %s", (call_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "message": "Call marked as resolved"})


@app.route('/api/calls/stats')
def call_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    types = ['Medical', 'Fire', 'Crime', 'Other']              
    stats = {}

    for t in types:
        cursor.execute("SELECT COUNT(*) FROM emergency_calls WHERE emergency_type = %s", (t,))
        stats[t] = cursor.fetchone()[0]

    cursor.close()
    conn.close()
    return jsonify({"status": "success", "type_stats": stats})


@app.route("/answer", methods=['GET', 'POST'])
def answer_call():
    resp = VoiceResponse()
    resp.say("Hi, please state the emergency", voice='alice')
    resp.record(maxLength="120", action="/handle-recording")
    resp.say("Thank you for your message. Goodbye.", voice='alice')
    return str(resp)

@app.route("/handle-recording", methods=['GET', 'POST'])
def handle_recording():
    API_KEY = "8f0cb68b51434eb5a1dd5af7b4c93176"
    TWILIO_SID = "ACcd9f88833ecd42eaa34bd32da8c61097"
    TWILIO_AUTH_TOKEN = "e15061e6780ad9581e94ad04f24dc9e6"
    time.sleep(10)

    headers = {
        "authorization": API_KEY,
        "content-type": "application/json"
    }

    def download_twilio_recording(recording_url):
        response = requests.get(recording_url, auth=(TWILIO_SID, TWILIO_AUTH_TOKEN))
        response.raise_for_status()
        return response.content

    def upload_audio_bytes(audio_bytes):
        upload_url = f"{base_url}/upload"
        response = requests.post(upload_url, headers={"authorization": API_KEY}, data=audio_bytes)
        response.raise_for_status()
        return response.json()["upload_url"]

    def request_transcription(audio_url):
        response = requests.post(f"{base_url}/transcript", json={"audio_url": audio_url}, headers=headers)
        response.raise_for_status()
        return response.json()["id"]

    def get_transcription_result(transcript_id):
        endpoint = f"{base_url}/transcript/{transcript_id}"
        while True:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data["status"] == "completed":
                return data["text"]
            elif data["status"] == "error":
                raise RuntimeError(f"Transcription failed: {data['error']}")
            else:
                time.sleep(3)

    recording_url = request.form['RecordingUrl']
    audio_bytes = download_twilio_recording(recording_url)
    audio_url = upload_audio_bytes(audio_bytes)
    transcript_id = request_transcription(audio_url)
    transcription_text = get_transcription_result(transcript_id)
    import mysql.connector
    import json
    import re

    chatgpt = send_req(transcription_text)
    print(chatgpt)
    clean_json = re.sub(r"^```(?:json)?|```$", "", chatgpt.strip(), flags=re.IGNORECASE).strip()


    try:
        # Convert to Python dict
        data = json.loads(clean_json)

        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='mysql'
        )
        cursor = conn.cursor()

        query = """
            INSERT INTO emergency_calls 
            (name, location, emergency_type, priority, time, status, reply_message) 
            VALUES (%s, %s, %s, %s, NOW(), %s, %s)
        """
        from datetime import datetime

        current_datetime = datetime.now()
        messgae_time = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        values = (
            data['name'],
            data['location'],
            data['emergency_type'],
            data['priority'],
            'active',  # initial status
            messgae_time
        )

        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Data inserted into MySQL")

    except Exception as e:
        print("❌ Error inserting into DB:", e)


    return "OK"

def run():
    app.run(host='0.0.0.0', port=80, debug=True)

def keep_alive():
    t = Thread(target=run)
    t.start()

def start_ngrok():
    try:
        ngrok_path = "ngrok-v3-stable-windows-amd64/ngrok.exe"
        subprocess.Popen([ngrok_path, "http", "80"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        time.sleep(4)
        tunnels = requests.get("http://localhost:4040/api/tunnels").json()['tunnels']
        return tunnels[0]['public_url']
    except Exception as e:
        print("Error starting ngrok:", e)
        return None

if __name__ == "__main__":
    public_url = ngrok.connect(80)
    print(" * ngrok tunnel available at:", public_url)
    app.run(host="0.0.0.0", port=80)
    keep_alive()