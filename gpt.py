import requests

API_KEY = ""  # replace with your Gemini API key

def send_req(transcribed_text=""):
    if not transcribed_text:
        return False

    print("Sending request to Google Gemini API")

    prompt = (
        "Extract the emergency type, location, and priority from the following message. "
        "Your response must be in this JSON format: "
        "{name, location, emergency_type, priority, reply_msg}. "
        "Available emergency_types=['Medical','Fire','Crime', 'Other']. "
        "Available priority=['high', 'medium', 'low']. "
        "priority for medical and fire is High,crime is medium,Other is low"
        f"Prompt: {transcribed_text}"
    )

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(f"{url}?key={API_KEY}", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        # Extract generated text from Gemini response (example structure)
        # Adjust this if the Gemini API response format is different
        generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
        return generated_text
    

    except Exception as e:
        print(f"Google Gemini API error: {e}")
        return None

'''
{
    name:aiyan
    location:bengaluru
    emergency:amb
    priority:high
}
'''
