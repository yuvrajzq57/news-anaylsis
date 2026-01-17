
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    print("Error: GROQ_API_KEY not found")
    exit(1)

url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        models = response.json()['data']
        with open('models.txt', 'w') as f:
            for model in models:
                f.write(f"{model['id']}\n")
        print("Models saved to models.txt")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Exception: {e}")
