
"""
BuyWiseIndia - FINAL Fixed for Render Web Service (FREE)
Telegram: @buywiseindia -> FB: buywiseindia26
Supports: Text + 1 to 10 Images + Link as it is
"""

import time
import os
import requests
from collections import defaultdict
import json
import threading
from flask import Flask

# Flask app - Render free hosting ke liye zaruri
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 WiseIndia Bot is Running! Telegram: buywiseindia -> FB: buywiseindia26 | Logs me check karo"

@app.route('/health')
def health():
    return "OK"

# ========= CONFIG - Env se lega =========
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8958443918:AAEv9E6La2AbRajLnbg7RL1nNasELGsksjE")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "335291736329653")
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "EAAUXbjVZBDeUBSz7U8POW8tL4DOBwkvlCJnPWyZAsYZButZBOH64wztNfARnGaaXGywOmdg0HyFZAqOS8KHoUaIPwPDp3lbVbjW1wdgpQVZAjt3hB5iuhhxD7ei1FGuXYVCtiwm9ZAqQYvhYRAmkxdD28u14RlXqGjZAW1LfseTlmrFIHK7GdQc4qZCMrozTxe8G8w5eGbIMcRcC49RZC4x2QR7USRZAA0tIcrDSvHf1nviVjLMsD4ZAhIFYmZCFlTEQJAVUHBkPxu9LHtuKxZAWL1KgFB")
# Optional channel ID, but username se bhi kaam karega
TELEGRAM_CHANNEL_ID_ENV = os.environ.get("TELEGRAM_CHANNEL_ID", "BUYWISEINDIA")

ALLOWED_CHANNEL_IDS = [TELEGRAM_CHANNEL_ID_ENV] if TELEGRAM_CHANNEL_ID_ENV else []
ALLOWED_USERNAMES = ["buywiseindia"]

media_buffer = defaultdict(list)
media_buffer_time = {}

def get_file_url(file_id):
    try:
        if not TELEGRAM_BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN missing in Env!")
            return None
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        r = requests.get(url, timeout=20).json()
        if r.get("ok"):
            file_path = r["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        else:
            print(f"getFile error: {r}")
    except Exception as e:
        print(f"File URL error: {e}")
    return None

def upload_fb_unpublished(image_url):
    try:
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
        data = {"url": image_url, "published": "false", "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
        r = requests.post(url, data=data, timeout=30).json()
        if "id" in r:
            return r["id"]
        else:
            print(f"FB unpublished upload error: {r}")
    except Exception as e:
        print(f"FB upload exception: {e}")
    return None

def post_fb_multi_photos(message, image_urls):
    try:
        if not FACEBOOK_PAGE_ID or not FACEBOOK_PAGE_ACCESS_TOKEN:
            print("❌ FB Page ID / Token missing in Env!")
            return False
            
        if not image_urls:
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
            data = {"message": message, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
            r = requests.post(url, data=data, timeout=30).json()
            print(f"FB Text Post Result: {r}")
            return "id" in r

        if len(image_urls) == 1:
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
            data = {"url": image_urls[0], "caption": message, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
            r = requests.post(url, data=data, timeout=30).json()
            print(f"FB Single Photo Result: {r}")
            return "id" in r

        print(f"📸 {len(image_urls)} images ka album mila, uploading to FB...")
        fb_ids = []
        for img_url in image_urls:
            fid = upload_fb_unpublished(img_url)
            if fid:
                fb_ids.append(fid)
            time.sleep(1)

        if not fb_ids:
            print("❌ Koi image FB pe upload nahi hui")
            return False

        attached_media = [{"media_fbid": fid} for fid in fb_ids]
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
        data = {
            "message": message,
            "attached_media": json.dumps(attached_media),
            "access_token": FACEBOOK_PAGE_ACCESS_TOKEN
        }
        r = requests.post(url, data=data, timeout=30).json()
        print(f"FB Multi-Photo Result: {r}")
        return "id" in r
    except Exception as e:
        print(f"post_fb error: {e}")
        return False

def get_telegram_updates(offset=0):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {"offset": offset, "timeout": 20}
        r = requests.get(url, params=params, timeout=25).json()
        return r
    except Exception as e:
        print(f"getUpdates error: {e}")
        return None

def process_telegram_post(post):
    text = post.get("text") or post.get("caption") or ""
    image_urls = []
    if "photo" in post:
        file_id = post["photo"][-1]["file_id"]
        f_url = get_file_url(file_id)
        if f_url:
            image_urls.append(f_url)
    return text, image_urls

def is_allowed_channel(post):
    chat = post.get("chat", {})
    chat_id = str(chat.get("id", ""))
    username = chat.get("username", "")
    # Username check - main
    if username in ALLOWED_USERNAMES:
        return True
    # ID check - agar diya hai to
    if chat_id and chat_id in ALLOWED_CHANNEL_IDS:
        return True
    # Agar env me ID nahi diya to username se hi allow (tera case)
    if not ALLOWED_CHANNEL_IDS and username == "buywiseindia":
        return True
    return False

def run_superagent():
    print("🚀 BuyFacebookBot Started - FINAL FIX")
    print(f"Watching: {ALLOWED_USERNAMES} -> FB Page: {FACEBOOK_PAGE_ID}")
    print(f"Bot Token set: {'YES' if TELEGRAM_BOT_TOKEN else 'NO - Env me daal'}")
    print(f"FB Token set: {'YES' if FACEBOOK_PAGE_ACCESS_TOKEN else 'NO - Env me daal'}")
    
    if not TELEGRAM_BOT_TOKEN or not FACEBOOK_PAGE_ACCESS_TOKEN:
        print("⚠️ Env vars missing hai, bot kaam nahi karega. Render -> Environment me daal.")
        return

    last_update_id = 0
    while True:
        try:
            updates = get_telegram_updates(offset=last_update_id+1)
            if not updates or not updates.get("ok"):
                time.sleep(3)
                continue

            for update in updates.get("result", []):
                last_update_id = update["update_id"]
                post = update.get("channel_post") or update.get("message")
                if not post:
                    continue

                chat = post.get("chat", {})
                # Debug - har post dikhega
                print(f"DEBUG: Post aaya - chat_id: {chat.get('id')} username: {chat.get('username')} text: {(post.get('text') or post.get('caption') or '')[:30]}")

                if not is_allowed_channel(post):
                    print(f"  -> Skip (allowed me nahi hai)")
                    continue

                media_group_id = post.get("media_group_id")
                if media_group_id:
                    media_buffer[media_group_id].append(post)
                    media_buffer_time[media_group_id] = time.time()
                    print(f"📦 Album part aaya: {media_group_id} - total {len(media_buffer[media_group_id])}")
                else:
                    text, img_urls = process_telegram_post(post)
                    if text or img_urls:
                        print(f"📩 Single post: {text[:60]}... Images: {len(img_urls)}")
                        post_fb_multi_photos(text, img_urls)

            # Album buffer check - 4 sec purane albums ko post karo
            current_time = time.time()
            to_delete = []
            for mg_id, posts in list(media_buffer.items()):
                if current_time - media_buffer_time.get(mg_id, 0) > 4:
                    all_text = ""
                    all_images = []
                    for p in posts:
                        t, imgs = process_telegram_post(p)
                        if t and not all_text:
                            all_text = t
                        all_images.extend(imgs)
                    print(f"📤 Album complete {mg_id}: {len(all_images)} photos + text: {all_text[:60]}")
                    post_fb_multi_photos(all_text, all_images)
                    to_delete.append(mg_id)
            
            for mg_id in to_delete:
                del media_buffer[mg_id]
                del media_buffer_time[mg_id]

            time.sleep(2)
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)

# Bot ko background thread me start karo - gunicorn ke liye bhi kaam karega
def start_bot_thread():
    time.sleep(3)
    run_superagent()

print("🌐 Starting bot thread...")
bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Web server starting on port {port}")
    app.run(host='0.0.0.0', port=port)
