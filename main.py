"""
BuyWiseIndia - Telegram → Facebook Auto Poster
Channel: https://t.me/buywiseindia
Page: https://www.facebook.com/buywiseindia26

Final SuperAgent - Text + Multi Images + Link as it is

SETUP (2 min):
1. Telegram: @BotFather pe ja, /newbot → token milega → neeche daal
2. Us bot ko https://t.me/buywiseindia me Admin bana (Post Messages permission)
3. Facebook: https://developers.facebook.com/tools/explorer/
   - App select kar → Get Page Access Token → Page: buywiseindia26 select
   - Permission: pages_manage_posts, pages_read_engagement, pages_show_list
   - Token copy karke neeche daal
"""

import time
import requests
from collections import defaultdict
import json

# ========= CONFIG - BuyWiseIndia ke liye pre-filled =========
TELEGRAM_BOT_TOKEN = "8958443918:AAEv9E6La2AbRajLnbg7RL1nNasELGsksjE"

# Tere channels - ID wala method (confusion khatam)
# ID kaise milega: @userinfobot pe channel ka post forward kar
# Abhi ke liye username se bhi kaam chalega
ALLOWED_CHANNEL_IDS = []  # jaise "-1001234567890" - ye best hai
ALLOWED_USERNAMES = ["buywiseindia"]  # https://t.me/buywiseindia

FACEBOOK_PAGE_ID = "buywiseindia26"  # https://www.facebook.com/buywiseindia26
# Agar numeric ID chahiye to: https://findmyfbid.in/ pe page link daal ke nikal le
FACEBOOK_PAGE_ACCESS_TOKEN = "EAAUXbjVZBDeUBS4jGHH4ZAG9qtPARWrGJ8Q3hy07HdB9XIHDTurSmW9K8SD6Akx0ZBoD4mYVysn6x5WVpHH2X4TKSaTK88e5JF0axOt2nxX99RhNZCQmWkqUPxnkzca4UZAGRdtZCZBwOSuUxNsR3U0DvdaCB2Qnr96hvXa9hytKCZAAkL5fWZC9LCYOjrMO6I5jOZCaSTOGLUMNUZCCzgZB2HBizTYoTJnPzKyMPHIBng66RbGN7NiC51niR7QYcoOIgHdUClwjo19MDRxiyuSwLSep"
# =============================================================

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
    data = {
        "url": image_url,
        "published": "false",
        "access_token": FACEBOOK_PAGE_ACCESS_TOKEN
    }
    try:
        r = requests.post(url, data=data, timeout=30).json()
        if "id" in r:
            print(f"  - Image uploaded: {r['id']}")
            return r["id"]
        else:
            print(f"  - FB upload error: {r}")
    except Exception as e:
        print(f"  - FB exception: {e}")
    return None

def post_fb_multi_photos(message, image_urls):
    if not image_urls:
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
        data = {"message": message, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
        r = requests.post(url, data=data, timeout=30).json()
        print(f"✅ FB Text Post: {r.get('id', r)}")
        return "id" in r

    if len(image_urls) == 1:
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
        data = {"url": image_urls[0], "caption": message, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
        r = requests.post(url, data=data, timeout=30).json()
        print(f"✅ FB Single Photo: {r.get('id', r)}")
        return "id" in r

    print(f"📸 Album: {len(image_urls)} photos mili, FB pe upload kar raha hu...")
    fb_ids = []
    for img_url in image_urls:
        fid = upload_fb_unpublished(img_url)
        if fid:
            fb_ids.append(fid)
        time.sleep(1.2)

    if not fb_ids:
        print("❌ Koi image upload nahi hui")
        return False

    attached_media = [{"media_fbid": fid} for fid in fb_ids]
    url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
    data = {
        "message": message,
        "attached_media": json.dumps(attached_media),
        "access_token": FACEBOOK_PAGE_ACCESS_TOKEN
    }
    r = requests.post(url, data=data, timeout=30).json()
    if "id" in r:
        print(f"✅ FB Multi-Photo Post Success: {r['id']} - {len(fb_ids)} photos")
    else:
        print(f"❌ FB Multi error: {r}")
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
    # ID se check (best)
    if ALLOWED_CHANNEL_IDS and chat_id in ALLOWED_CHANNEL_IDS:
        return True
    # Username se check (buywiseindia)
    if username in ALLOWED_USERNAMES:
        return True
    # Agar list khali hai to sab allow (testing ke liye)
    if not ALLOWED_CHANNEL_IDS and not ALLOWED_USERNAMES:
        return True
    return False

def run_superagent():
    print("🚀 BuyWiseIndia SuperAgent Started")
    print(f"Channel: https://t.me/buywiseindia → Page: https://www.facebook.com/buywiseindia26")
    print(f"Watching Usernames: {ALLOWED_USERNAMES} | IDs: {ALLOWED_CHANNEL_IDS}")
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
                print(f"📦 Album part: {media_group_id} - total {len(media_buffer[media_group_id])}")
            else:
                text, img_urls = process_telegram_post(post)
                if text or img_urls:
                    print(f"\n📩 New Post: {text[:80]}... | Images: {len(img_urls)}")
                    post_fb_multi_photos(text, img_urls)

        current_time = time.time()
        to_delete = []
        for mg_id, posts in list(media_buffer.items()):
            if current_time - media_buffer_time.get(mg_id, 0) > 3.5:
                all_text = ""
                all_images = []
                for p in posts:
                    t, imgs = process_telegram_post(p)
                    if t and not all_text:
                        all_text = t
                    all_images.extend(imgs)
                
                print(f"\n📤 Album Complete {mg_id}: {len(all_images)} photos")
                print(f"Text: {all_text[:100]}...")
                post_fb_multi_photos(all_text, all_images)
                to_delete.append(mg_id)
        
        for mg_id in to_delete:
            del media_buffer[mg_id]
            del media_buffer_time[mg_id]

        time.sleep(2)

if __name__ == "__main__":
    if "YOUR_" in TELEGRAM_BOT_TOKEN or "YOUR_" in FACEBOOK_PAGE_ACCESS_TOKEN:
        print("❗ Pehle TELEGRAM_BOT_TOKEN aur FACEBOOK_PAGE_ACCESS_TOKEN daal de file me")
        print("Telegram: @BotFather | Facebook: developers.facebook.com/tools/explorer/")
    else:
        run_superagent()
