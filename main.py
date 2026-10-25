
"""
BuyWiseIndia - DEBUG VERSION - Error dikhayega
"""

import time
import os
import sys
import requests
from collections import defaultdict
import json
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Bot Running - Check logs for DEBUG"

@app.route('/health')
def health():
    return "OK"

# Env se lega
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8958443918:AAEv9E6La2AbRajLnbg7RL1nNasELGsksjE").strip()
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "335291736329653").strip()
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "EAAUXbjVZBDeUBS6NBZBwy4FqdBuIy997OfVE8gxsFepezI0ULxKrCncClZC70okUfcyGmI7smPe1yMHPECOZCn3Pt7ANUDIX9K4HlcrZC9UHVctKObkLxHVTZCMimFrRF7ZCI2GB7ABkCAlC9cLZAalBxUlMQZBOpYls94QFxZAOUnPEua9ZCOZCqeJxtZA4kVwDbXkiCspSUV13gn9kqMEPg4Kc1ZCiUCsQ2mNTJvyQZDZD").strip()
TELEGRAM_CHANNEL_ID_ENV = os.environ.get("TELEGRAM_CHANNEL_ID", "buywiseindia").strip()

print(f"🔍 ENV CHECK at import:", flush=True)
print(f"  TELEGRAM_BOT_TOKEN: {'SET ('+TELEGRAM_BOT_TOKEN[:10]+'...)' if TELEGRAM_BOT_TOKEN else 'NOT SET'}", flush=True)
print(f"  FACEBOOK_PAGE_ID: {FACEBOOK_PAGE_ID if FACEBOOK_PAGE_ID else 'NOT SET'}", flush=True)
print(f"  FACEBOOK_PAGE_ACCESS_TOKEN: {'SET ('+FACEBOOK_PAGE_ACCESS_TOKEN[:15]+'...)' if FACEBOOK_PAGE_ACCESS_TOKEN else 'NOT SET'}", flush=True)
print(f"  TELEGRAM_CHANNEL_ID: {TELEGRAM_CHANNEL_ID_ENV}", flush=True)

ALLOWED_CHANNEL_IDS = [TELEGRAM_CHANNEL_ID_ENV] if TELEGRAM_CHANNEL_ID_ENV else []
ALLOWED_USERNAMES = ["buywiseindia", "BUYWISEINDIA", "BuyWiseIndia"]

media_buffer = defaultdict(list)
media_buffer_time = {}

def get_file_url(file_id):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        r = requests.get(url, timeout=20).json()
        print(f"getFile response: {r}", flush=True)
        if r.get("ok"):
            file_path = r["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    except Exception as e:
        print(f"File URL error: {e}", flush=True)
    return None

def upload_fb_unpublished(image_url):
    try:
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
        data = {"url": image_url, "published": "false", "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
        print(f"Uploading to FB unpublished: {image_url[:50]}...", flush=True)
        r = requests.post(url, data=data, timeout=30).json()
        print(f"FB unpublished result: {r}", flush=True)
        if "id" in r:
            return r["id"]
    except Exception as e:
        print(f"FB upload exception: {e}", flush=True)
    return None

def post_fb_multi_photos(message, image_urls):
    try:
        print(f"Attempting FB post - Message: {message[:50]} Images: {len(image_urls)}", flush=True)
        print(f"FB Page ID: {FACEBOOK_PAGE_ID}", flush=True)
        
        if not image_urls:
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
            data = {"message": message, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
            r = requests.post(url, data=data, timeout=30).json()
            print(f"FB Text Post Result: {r}", flush=True)
            return "id" in r

        if len(image_urls) == 1:
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
            data = {"url": image_urls[0], "caption": message, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
            r = requests.post(url, data=data, timeout=30).json()
            print(f"FB Single Photo Result: {r}", flush=True)
            return "id" in r

        print(f"📸 {len(image_urls)} images album", flush=True)
        fb_ids = []
        for img_url in image_urls:
            fid = upload_fb_unpublished(img_url)
            if fid:
                fb_ids.append(fid)
            time.sleep(1)

        if not fb_ids:
            print("❌ No image uploaded", flush=True)
            return False

        attached_media = [{"media_fbid": fid} for fid in fb_ids]
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
        data = {
            "message": message,
            "attached_media": json.dumps(attached_media),
            "access_token": FACEBOOK_PAGE_ACCESS_TOKEN
        }
        r = requests.post(url, data=data, timeout=30).json()
        print(f"FB Multi Result: {r}", flush=True)
        return "id" in r
    except Exception as e:
        print(f"post_fb error: {e}", flush=True)
        return False

def get_telegram_updates(offset=0):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {"offset": offset, "timeout": 20}
        r = requests.get(url, params=params, timeout=25)
        j = r.json()
        if not j.get("ok"):
            print(f"Telegram getUpdates error: {j}", flush=True)
        return j
    except Exception as e:
        print(f"getUpdates exception: {e}", flush=True)
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
    print(f"Checking channel - chat_id: {chat_id} username: {username}", flush=True)
    # Username check - case insensitive
    if username and username.lower() == "buywiseindia":
        return True
    if chat_id and chat_id in ALLOWED_CHANNEL_IDS:
        return True
    if not ALLOWED_CHANNEL_IDS and username.lower() == "buywiseindia":
        return True
    return False

def run_superagent():
    print("🚀 BuyFacebookBot Started - DEBUG MODE", flush=True)
    print(f"Watching: {ALLOWED_USERNAMES} -> FB Page: {FACEBOOK_PAGE_ID}", flush=True)
    print(f"Bot Token set: {'YES' if TELEGRAM_BOT_TOKEN else 'NO'}", flush=True)
    print(f"FB Token set: {'YES' if FACEBOOK_PAGE_ACCESS_TOKEN else 'NO'}", flush=True)
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN missing!", flush=True)
        return
    if not FACEBOOK_PAGE_ACCESS_TOKEN:
        print("❌ FACEBOOK_PAGE_ACCESS_TOKEN missing!", flush=True)
        return
    if not FACEBOOK_PAGE_ID:
        print("❌ FACEBOOK_PAGE_ID missing!", flush=True)
        return

    # Test Telegram token
    try:
        test_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        r = requests.get(test_url, timeout=10).json()
        print(f"Telegram getMe: {r}", flush=True)
        if not r.get("ok"):
            print(f"❌ Invalid Telegram token! getMe failed: {r}", flush=True)
            return
    except Exception as e:
        print(f"getMe error: {e}", flush=True)

    last_update_id = 0
    print("🔄 Starting polling loop...", flush=True)
    while True:
        try:
            updates = get_telegram_updates(offset=last_update_id+1)
            if not updates or not updates.get("ok"):
                time.sleep(3)
                continue

            results = updates.get("result", [])
            if results:
                print(f"📥 Got {len(results)} updates", flush=True)

            for update in results:
                last_update_id = update["update_id"]
                post = update.get("channel_post") or update.get("message")
                if not post:
                    print(f"Skip update {last_update_id} - no channel_post/message: {update}", flush=True)
                    continue

                chat = post.get("chat", {})
                print(f"DEBUG: Post aaya - chat_id: {chat.get('id')} username: {chat.get('username')} text: {(post.get('text') or post.get('caption') or '')[:40]}", flush=True)

                if not is_allowed_channel(post):
                    print(f"  -> Skip (allowed list me nahi hai)", flush=True)
                    continue

                media_group_id = post.get("media_group_id")
                if media_group_id:
                    media_buffer[media_group_id].append(post)
                    media_buffer_time[media_group_id] = time.time()
                    print(f"📦 Album part: {media_group_id}", flush=True)
                else:
                    text, img_urls = process_telegram_post(post)
                    if text or img_urls:
                        print(f"📩 Single post: {text[:60]}... Images: {len(img_urls)}", flush=True)
                        success = post_fb_multi_photos(text, img_urls)
                        print(f"Post success: {success}", flush=True)

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
                    print(f"📤 Album complete {mg_id}: {len(all_images)} photos", flush=True)
                    post_fb_multi_photos(all_text, all_images)
                    to_delete.append(mg_id)
            
            for mg_id in to_delete:
                del media_buffer[mg_id]
                del media_buffer_time[mg_id]

            time.sleep(2)
        except Exception as e:
            print(f"Loop error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            time.sleep(5)

def start_bot_thread():
    print("⏳ Bot thread sleeping 3 sec...", flush=True)
    time.sleep(3)
    run_superagent()

print("🌐 Starting bot thread...", flush=True)
bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Web server starting on port {port}", flush=True)
    app.run(host='0.0.0.0', port=port)
