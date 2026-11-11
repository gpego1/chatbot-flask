import requests

class EvolutionAPI:
    def __init__(self):
        pass

    def send_message(self, instance_name, apiKey, sender_number, message):
        url = f"http://localhost:8080/message/sendText/{instance_name}"
        payload = {
            "number": sender_number,
            "textMessage": message,
            "delay": 123,
            "quoted": {},
            "linkPreview": True,
            "mentioned": ["<string>"]
        }
        headers = {
            "apikey": apiKey,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)