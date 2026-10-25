"""
BuyWiseIndia - FREE Hosting ke liye (Render Web Service)
Background Worker ka free khatam, Web Service free hai

Ye file Web Service pe chalegi - free me
"""

import time
import os
import requests
from collections import defaultdict
import json
import threading
from flask import Flask

# Flask app - Render ko lagta hai ye web service hai (free ke liye zaruri)
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 BuyWiseIndia Bot is Running! Telegram: buywiseindia -> FB: buywiseindia26"

@app.route('/health')
def health():
    return "OK"

# ========= CONFIG =========
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8958443918:AAEv9E6La2AbRajLnbg7RL1nNasELGsksjE")
ALLOWED_CHANNEL_IDS = [os.environ.get("TELEGRAM_CHANNEL_ID", "-1001234567890")]
ALLOWED_USERNAMES = ["BUYWISEINDIA"]
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "buywiseindia26")
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "EAAUXbjVZBDeUBS4jGHH4ZAG9qtPARWrGJ8Q3hy07HdB9XIHDTurSmW9K8SD6Akx0ZBoD4mYVysn6x5WVpHH2X4TKSaTK88e5JF0axOt2nxX99RhNZCQmWkqUPxnkzca4UZAGRdtZCZBwOSuUxNsR3U0DvdaCB2Qnr96hvXa9hytKCZAAkL5fWZC9LCYOjrMO6I5jOZCaSTOGLUMNUZCCzgZB2HBizTYoTJnPzKyMPHIBng66RbGN7NiC51niR7QYcoOIgHdUClwjo19MDRxiyuSwLSep")

media_buffer = defaultdict(list)
media_buffer_time = {}

def get_file_url(file_id):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        r = requests.get(url, timeout=20).json()
        if r.get("ok"):
            file_path = r["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    except Exception as e:
        print(f"File URL error: {e}")
    return None

def upload_fb_unpublished(image_url):
    url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
    data = {"url": image_url, "published": "false", "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
    try:
        r = requests.post(url, data=data, timeout=30).json()
        if "id" in r:
            return r["id"]
        else:
            print(f"FB error: {r}")
    except Exception as e:
        print(f"FB exception: {e}")
    return None

def post_fb_multi_photos(message, image_urls):
    if not image_urls:
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
        data = {"message": message, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
        r = requests.post(url, data=data, timeout=30).json()
        print(f"FB Text Post: {r}")
        return "id" in r
    if len(image_urls) == 1:
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
        data = {"url": image_urls[0], "caption": message, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
        r = requests.post(url, data=data, timeout=30).json()
        print(f"FB Single Photo: {r}")
        return "id" in r
    print(f"📸 {len(image_urls)} images ka album mila")
    fb_ids = []
    for img_url in image_urls:
        fid = upload_fb_unpublished(img_url)
        if fid:
            fb_ids.append(fid)
        time.sleep(1)
    if not fb_ids:
        print("❌ Koi image upload nahi hui")
        return False
    attached_media = [{"media_fbid": fid} for fid in fb_ids]
    url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
    data = {"message": message, "attached_media": json.dumps(attached_media), "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
    r = requests.post(url, data=data, timeout=30).json()
    print(f"FB Multi Result: {r}")
    return "id" in r

def get_telegram_updates(offset=0):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 20}
    try:
        r = requests.get(url, params=params, timeout=25).json()
        return r
    except:
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
    if chat_id in ALLOWED_CHANNEL_IDS:
        return True
    if username in ALLOWED_USERNAMES:
        return True
    return False

def run_superagent():
    print("🚀 BuyFacebookBot Started - FREE Web Service Mode")
    print(f"Watching: {ALLOWED_USERNAMES} -> Posting to: {FACEBOOK_PAGE_ID}")
    last_update_id = 0
    while True:
        updates = get_telegram_updates(offset=last_update_id+1)
        if not updates or not updates.get("ok"):
            time.sleep(3)
            continue
        for update in updates.get("result", []):
            last_update_id = update["update_id"]
            post = update.get("channel_post") or update.get("message")
            if not post:
                continue
            if not is_allowed_channel(post):
                continue
            media_group_id = post.get("media_group_id")
            if media_group_id:
                media_buffer[media_group_id].append(post)
                media_buffer_time[media_group_id] = time.time()
                print(f"📦 Album part: {media_group_id}")
            else:
                text, img_urls = process_telegram_post(post)
                if text or img_urls:
                    print(f"📩 Single: {text[:60]}... Images: {len(img_urls)}")
                    post_fb_multi_photos(text, img_urls)
        current_time = time.time()
        to_delete = []
        for mg_id, posts in list(media_buffer.items()):
            if current_time - media_buffer_time.get(mg_id, 0) > 3:
                all_text = ""
                all_images = []
                for p in posts:
                    t, imgs = process_telegram_post(p)
                    if t and not all_text:
                        all_text = t
                    all_images.extend(imgs)
                print(f"📤 Album complete: {len(all_images)} photos")
                post_fb_multi_photos(all_text, all_images)
                to_delete.append(mg_id)
        for mg_id in to_delete:
            del media_buffer[mg_id]
            del media_buffer_time[mg_id]
        time.sleep(2)

# Bot ko background thread me chalao
def start_bot_thread():
    time.sleep(2)
    run_superagent()

if __name__ == "__main__":
    # Bot thread start
    bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
    bot_thread.start()
    # Flask web server start - Render isko free samjhega
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Web server starting on port {port} - FREE mode")
    app.run(host='0.0.0.0', port=port)
