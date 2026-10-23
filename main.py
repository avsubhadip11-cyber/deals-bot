import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()

import os
import re
import urllib.request
import urllib.parse
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = 39216234
API_HASH = "34be32a21b4686f082dcfe8e200bfb5c"
SESSION_STRING = os.environ.get("SESSION_STRING")

SOURCE_NAME = "EagleTek Shopping Deals"
DEST_CHANNEL = "PocketSaveDeals"
AMAZON_TAG = "subhadip0b28-21"
EARNKARO_USER_ID = "327267"

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def get_final_url(url):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            return response.geturl()
    except Exception:
        return url

def get_clean_product_image(url):
    asin_match = re.search(r'/(?:dp|gp/product|d)/([A-Z0-9]{10})', url, re.I)
    if asin_match:
        asin = asin_match.group(1)
        return f"https://images-na.ssl-images-amazon.com/images/P/{asin}.01._SCLZZZZZZZ_.jpg"
        
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', html, re.I)
        if not m:
            m = re.search(r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:image["\']', html, re.I)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None

def clean_and_tag_amazon(url):
    final_url = get_final_url(url)
    asin_match = re.search(r'/(?:dp|gp/product|d)/([A-Z0-9]{10})', final_url, re.I)
    if asin_match:
        asin = asin_match.group(1)
        return f"https://www.amazon.in/dp/{asin}?tag={AMAZON_TAG}"
    base_url = final_url.split('?')[0]
    return f"{base_url}?tag={AMAZON_TAG}"

def convert_to_earnkaro(url):
    final_url = get_final_url(url)
    encoded_url = urllib.parse.quote_plus(final_url)
    return f"https://earnkaro.com/deal?r={EARNKARO_USER_ID}&url={encoded_url}"

def process_message(text):
    if not text:
        return text, None
    pattern = r'https?://[^\s]+'
    earnkaro_domains = [
        "flipkart.com", "fkrt.it", "dl.flipkart.com", "shopsy.in",
        "myntra.com", "myntr.it", "ajio.com", "ajiio.in",
        "nykaa.com", "nykaa.ly", "tatacliq.com", "jiomart.com",
        "croma.com", "boat-lifestyle.com", "mamaearth.in"
    ]
    first_target_url = None

    def replacer(match):
        nonlocal first_target_url
        raw_url = match.group(0).rstrip('.,;()[]')
        lowered = raw_url.lower()
        if any(d in lowered for d in ["amazon.", "amzn.to", "link.amazon"]):
            res = clean_and_tag_amazon(raw_url)
            if not first_target_url:
                first_target_url = res
            return res
        elif any(d in lowered for d in earnkaro_domains):
            res = convert_to_earnkaro(raw_url)
            if not first_target_url:
                first_target_url = raw_url
            return res
        return raw_url
        
    modified_text = re.sub(pattern, replacer, text)
    return modified_text, first_target_url

async def main():
    await client.start()
    
    target_entity = None
    async for dialog in client.iter_dialogs():
        if dialog.name == SOURCE_NAME or getattr(dialog.entity, 'username', '') == "Loot_shoppingdeals23":
            target_entity = dialog.entity
            break
            
    if not target_entity:
        print(f"Error: Channel '{SOURCE_NAME}' not found!")
        return

    print(f"\n[+] Koyeb Worker Active! Monitoring: {target_entity.title}")

    @client.on(events.NewMessage(chats=target_entity))
    async def handler(event):
        original_text = event.message.text or ""
        modified_text, target_url = process_message(original_text)
        
        image_url = None
        if target_url:
            image_url = get_clean_product_image(target_url)

        try:
            if image_url:
                await client.send_file(DEST_CHANNEL, file=image_url, caption=modified_text)
            else:
                await client.send_message(DEST_CHANNEL, modified_text)
        except Exception as e:
            print(f"[-] Error: {e}")

    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
