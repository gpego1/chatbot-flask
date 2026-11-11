import requests

class EvolutionAPI:
    def __init__(self):
        pass

    def send_message(self, instance_name, api_secret, sender_number, message):
        url = f"http://localhost:8080/message/sendText/{instance_name}"
        payload = {
            "number": sender_number,
            "text": message,
            "delay": 2000,
            "linkPreview": True,
        }
        headers = {
            "apikey": api_secret,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response
