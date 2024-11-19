import requests
import os
from dotenv import load_dotenv

load_dotenv()

def create_paste(title, content):
    api_key = os.getenv("PASTEBIN_API_KEY")
    if not api_key:
        raise Exception("PASTEBIN_API_KEY not found in environment variables")

    url = 'https://pastebin.com/api/api_post.php'
    data = {
        'api_dev_key': api_key,
        'api_option': 'paste',
        'api_paste_code': content,
        'api_paste_private': '0',  # 0=public, 1=unlisted, 2=private
        'api_paste_name': title,
        'api_paste_expire_date': '1W'  # Expires in 1 week
    }

    response = requests.post(url, data=data)
    if response.status_code == 200 and not response.text.startswith('Bad API request'):
        return response.text
    else:
        raise Exception(f"Error creating paste: {response.text}")