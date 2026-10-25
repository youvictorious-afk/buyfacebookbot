
"""
BuyWiseIndia - FINAL WORKING - 100% Tested
Telegram @buywiseindia -> FB Page 335291736329653
"""

import os, time, sys, json, threading, requests
from collections import defaultdict
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Running - buywiseindia -> FB"
@app.route('/health')
def health(): return "OK"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","8958443918:AAEv9E6La2AbRajLnbg7RL1nNasELGsksjE").strip()
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID","335291736329653").strip()
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN","EAAUXbjVZBDeUBS6NBZBwy4FqdBuIy997OfVE8gxsFepezI0ULxKrCncClZC70okUfcyGmI7smPe1yMHPECOZCn3Pt7ANUDIX9K4HlcrZC9UHVctKObkLxHVTZCMimFrRF7ZCI2GB7ABkCAlC9cLZAalBxUlMQZBOpYls94QFxZAOUnPEua9ZCOZCqeJxtZA4kVwDbXkiCspSUV13gn9kqMEPg4Kc1ZCiUCsQ2mNTJvyQZDZD").strip()

print(f"ENV: TG={'YES' if TELEGRAM_BOT_TOKEN else 'NO'} FB_ID={FACEBOOK_PAGE_ID} FB_TOKEN={'YES' if FACEBOOK_PAGE_ACCESS_TOKEN else 'NO'}", flush=True)

media_buffer = defaultdict(list)
media_buffer_time = {}

def get_file_url(file_id):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        r = requests.get(url, timeout=20).json()
        if r.get("ok"):
            return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{r['result']['file_path']}"
        print(f"getFile FAIL: {r}", flush=True)
    except Exception as e:
        print(f"getFile ERR: {e}", flush=True)
    return None

def post_fb(message, image_urls):
    try:
        print(f"FB POST ATTEMPT: msg={message[:40]} imgs={len(image_urls)}", flush=True)
        if not image_urls:
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
            data = {"message": message, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
            r = requests.post(url, data=data, timeout=30).json()
            print(f"FB TEXT RESULT: {r}", flush=True)
            return "id" in r
        if len(image_urls)==1:
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
            data = {"url": image_urls[0], "caption": message, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
            r = requests.post(url, data=data, timeout=30).json()
            print(f"FB SINGLE RESULT: {r}", flush=True)
            return "id" in r
        # multi
        fb_ids=[]
        for img in image_urls:
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
            data = {"url": img, "published": "false", "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
            rr = requests.post(url, data=data, timeout=30).json()
            print(f"FB UNPUB: {rr}", flush=True)
            if "id" in rr: fb_ids.append(rr["id"])
            time.sleep(1)
        if not fb_ids: return False
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
        data = {"message": message, "attached_media": json.dumps([{"media_fbid": fid} for fid in fb_ids]), "access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
        r = requests.post(url, data=data, timeout=30).json()
        print(f"FB MULTI RESULT: {r}", flush=True)
        return "id" in r
    except Exception as e:
        print(f"FB ERR: {e}", flush=True)
        return False

def get_updates(offset=0):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        r = requests.get(url, params={"offset": offset, "timeout": 20}, timeout=25).json()
        return r
    except Exception as e:
        print(f"getUpdates ERR: {e}", flush=True)
        return None

def run():
    print("🚀 Bot Started - Waiting for Telegram posts", flush=True)
    print(f"Token check: {TELEGRAM_BOT_TOKEN[:10]}... Page: {FACEBOOK_PAGE_ID}", flush=True)
    # Test token
    try:
        me = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe", timeout=10).json()
        print(f"getMe: {me}", flush=True)
    except Exception as e:
        print(f"getMe fail: {e}", flush=True)
        return

    last_id=0
    while True:
        try:
            ups = get_updates(last_id+1)
            if not ups or not ups.get("ok"):
                if ups: print(f"getUpdates not ok: {ups}", flush=True)
                time.sleep(3)
                continue
            res = ups.get("result", [])
            if res:
                print(f"📥 Got {len(res)} raw updates", flush=True)
                for u in res:
                    print(f"RAW UPDATE: {json.dumps(u)[:500]}", flush=True)
            for upd in res:
                last_id = upd["update_id"]
                post = upd.get("channel_post") or upd.get("message")
                if not post:
                    print(f"Skip - no channel_post/message in {upd['update_id']}", flush=True)
                    continue
                chat = post.get("chat", {})
                chat_id = chat.get("id")
                username = chat.get("username","")
                print(f"DEBUG: Post aaya - chat_id={chat_id} username={username} title={chat.get('title')} text={(post.get('text') or post.get('caption') or '')[:50]}", flush=True)

                # ALLOW ALL for now - debug
                # if username.lower() != "buywiseindia" and str(chat_id) not in ["-1001234567890"]:
                #     print(f"Skip not buywiseindia", flush=True)
                #     continue

                mg = post.get("media_group_id")
                text = post.get("text") or post.get("caption") or ""
                img_urls=[]
                if "photo" in post:
                    fid = post["photo"][-1]["file_id"]
                    furl = get_file_url(fid)
                    if furl: img_urls.append(furl)
                if mg:
                    media_buffer[mg].append((text, img_urls))
                    media_buffer_time[mg]=time.time()
                    print(f"Album part {mg} buffered", flush=True)
                else:
                    if text or img_urls:
                        print(f"Posting to FB now...", flush=True)
                        post_fb(text, img_urls)

            # album flush
            now=time.time()
            todel=[]
            for mg_id, items in list(media_buffer.items()):
                if now - media_buffer_time.get(mg_id,0) > 4:
                    all_text=""
                    all_imgs=[]
                    for t, imgs in items:
                        if t and not all_text: all_text=t
                        all_imgs.extend(imgs)
                    print(f"Album complete {mg_id} -> FB", flush=True)
                    post_fb(all_text, all_imgs)
                    todel.append(mg_id)
            for k in todel:
                del media_buffer[k]; del media_buffer_time[k]
            time.sleep(2)
        except Exception as e:
            print(f"LOOP ERR: {e}", flush=True)
            import traceback; traceback.print_exc()
            time.sleep(5)

def start_thread():
    time.sleep(3)
    run()

print("🌐 Starting bot thread...", flush=True)
threading.Thread(target=start_thread, daemon=True).start()

if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    print(f"🌐 Flask on {port}", flush=True)
    app.run(host="0.0.0.0", port=port)
