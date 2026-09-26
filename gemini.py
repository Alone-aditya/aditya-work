#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==========================================
# Install requirements before running:
# pip install requests pyotp
# ==========================================

import requests
import time
import json
import os
import pyotp
import uuid
import csv

# ==========================================
# Configuration
# ==========================================
TOKEN = "8724962559:AAHdFRRozjlevTP7WQOhO9-LltGWkIDNU7c"  # <-- Replace with your bot token
ADMIN_ID = 6103314569          # <-- Replace with your Admin ID

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
DB_FILE = "database.json"

tg_session = requests.Session()

# Premium Emojis
PEM = {
  "ok": '<tg-emoji emoji-id="6111726981760423576">✅</tg-emoji>',
  "no": '<tg-emoji emoji-id="6311965254817423602">❌</tg-emoji>',
  "warn": '<tg-emoji emoji-id="6314510813214284503">⚠️</tg-emoji>',
  "admin": '<tg-emoji emoji-id="5353032893096567467">📊</tg-emoji>',
  "user": '<tg-emoji emoji-id="5352861489541714456">👤</tg-emoji>',
  "money": '<tg-emoji emoji-id="6111799373434197692">💸</tg-emoji>',
  "gift": '<tg-emoji emoji-id="6109561463544747928">🎁</tg-emoji>',
  "msg": '<tg-emoji emoji-id="5337302974806922068">💬</tg-emoji>',
  "cookie": '<tg-emoji emoji-id="6314402846326397461">🍪</tg-emoji>',
  "rocket": '<tg-emoji emoji-id="5352597830089347330">🚀</tg-emoji>',
  "target": '<tg-emoji emoji-id="6109432142079466939">🎯</tg-emoji>',
  "pin": '<tg-emoji emoji-id="6111410240807245099">📌</tg-emoji>',
  "hi": '<tg-emoji emoji-id="5353027129250453493">👋</tg-emoji>',
  "add": '<tg-emoji emoji-id="6188038822509418008">➕</tg-emoji>',
  "rem": '<tg-emoji emoji-id="6188343249791358585">➖</tg-emoji>',
  "view": '<tg-emoji emoji-id="6188447235244562676">👀</tg-emoji>',
  "key": '<tg-emoji emoji-id="6233302765582424442">🔑</tg-emoji>',
  "wait": '<tg-emoji emoji-id="6233136657722251031">⏳</tg-emoji>',
  "earn": '<tg-emoji emoji-id="6186175669991379791">🤑</tg-emoji>',
  "bell": '<tg-emoji emoji-id="6260082445018731350">🔔</tg-emoji>',
  "crown": '<tg-emoji emoji-id="6183661284467152997">👑</tg-emoji>',
  "gear": '<tg-emoji emoji-id="6260111633616475361">⚙️</tg-emoji>',
  "group": '<tg-emoji emoji-id="6233527959307688784">👥</tg-emoji>',
  "check": '<tg-emoji emoji-id="6188038822509418008">✅</tg-emoji>',
  "join": '<tg-emoji emoji-id="5352597830089347330">➡️</tg-emoji>'
}

# Databases
users = {}
submissions = []
rates = {"ig_2fa": 3.00, "fb_cookies": 4.50}
admin_settings = {
    "supportUrl": "https://t.me/adityaXwork_support",
    "withdrawMethods": [{"name": "bKash", "minAmount": 50}, {"name": "Nagad", "minAmount": 50}],
    "newUserGuide": {"type": "text", "text": "Read our guide to learn how to work."},
    "igGuide": {"type": "text", "text": "Instagram work rules will be displayed here."},
    "fbGuide": {"type": "text", "text": "Facebook work rules will be displayed here."},
    "referralTasksRequired": 5,
    "referralBonusAmount": 10.0
}
bot_username = "AdityaXwork_bot"

user_states = {}
user_current_task = {}
user_temp_data = {}

def load_db():
    global users, submissions, rates, admin_settings
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                users = {int(k): v for k, v in data.get("users", {}).items()}
                submissions = data.get("submissions", [])
                rates = data.get("rates", rates)
                admin_settings = data.get("admin_settings", admin_settings)
                if "referralTasksRequired" not in admin_settings:
                    admin_settings["referralTasksRequired"] = 5
                if "referralBonusAmount" not in admin_settings:
                    admin_settings["referralBonusAmount"] = 10.0
                if "admins" not in admin_settings:
                    admin_settings["admins"] = []
                if "must_join_channel" not in admin_settings:
                    admin_settings["must_join_channel"] = ""
                if "igGuide" not in admin_settings:
                    admin_settings["igGuide"] = {"type": "text", "text": "Instagram work rules will be displayed here."}
                if "fbGuide" not in admin_settings:
                    admin_settings["fbGuide"] = {"type": "text", "text": "Facebook work rules will be displayed here."}
        except:
            pass

def save_db():
    data = {
        "users": {str(k): v for k, v in users.items()},
        "submissions": submissions,
        "rates": rates,
        "admin_settings": admin_settings
    }
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except:
        pass

def is_admin(chat_id):
    if str(chat_id) == str(ADMIN_ID): return True
    return int(chat_id) in admin_settings.get("admins", [])

def check_force_sub(chat_id):
    channel = admin_settings.get("must_join_channel", "")
    if not channel:
        return True
    res = api_call("getChatMember", {"chat_id": channel, "user_id": chat_id})
    if not res.get("ok"):
        return False
    status = res["result"].get("status")
    return status in ["member", "administrator", "creator"]

def ask_force_sub(chat_id):
    channel = admin_settings.get("must_join_channel", "")
    kb = [
        [{"text": "Join Channel", "url": f"https://t.me/{channel.replace('@', '')}", "icon_custom_emoji_id": "5352597830089347330", "style": "primary"}],
        [{"text": "Joined", "callback_data": "check_sub", "icon_custom_emoji_id": "6188038822509418008", "style": "success"}]
    ]
    send_message(chat_id, f"{PEM['warn']} <b>Must Join Channel!</b>\nYou must join our channel to use this bot.", reply_markup={"inline_keyboard": kb})

def init_user(chat_id, username, first_name, referrer_id=None):
    if chat_id not in users:
        ref = None
        if referrer_id and referrer_id.isdigit():
            ref_int = int(referrer_id)
            if ref_int != chat_id:
                ref = ref_int
        users[chat_id] = {
            "id": chat_id,
            "username": username,
            "first_name": first_name,
            "balance": 0.0,
            "totalEarned": 0.0,
            "joinedAt": time.time(),
            "referredBy": ref,
            "referralBonusPaid": False
        }
        save_db()
    else:
        updated = False
        if users[chat_id].get("username") != username:
            users[chat_id]["username"] = username
            updated = True
        if users[chat_id].get("first_name") != first_name:
            users[chat_id]["first_name"] = first_name
            updated = True
        if updated:
            save_db()

# --- API Methods ---
def api_call(method, payload=None):
    url = f"{BASE_URL}/{method}"
    try:
        if payload:
            res = tg_session.post(url, json=payload, timeout=60)
        else:
            res = tg_session.get(url, timeout=60)
        return res.json()
    except Exception:
        return {}

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api_call("sendMessage", payload)

def send_document(chat_id, document_path):
    url = f"{BASE_URL}/sendDocument"
    try:
        with open(document_path, "rb") as f:
            res = tg_session.post(url, data={"chat_id": chat_id}, files={"document": f}, timeout=60)
        return res.json()
    except Exception:
        return {}

def download_file(file_id, save_path):
    res = api_call("getFile", {"file_id": file_id})
    if res.get("ok"):
        file_path = res["result"].get("file_path")
        url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        try:
            r = tg_session.get(url, timeout=60)
            if r.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(r.content)
                return True
        except Exception:
            pass
    return False

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api_call("editMessageText", payload)

def delete_message(chat_id, message_id):
    return api_call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def answer_callback(callback_id, text="", show_alert=False):
    api_call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text, "show_alert": show_alert})

# --- Keyboards ---

def getMainMenu():
    return {
        "keyboard": [
            [
                {"text": "Work", "icon_custom_emoji_id": "6111410240807245099", "style": "primary"}, 
                {"text": "Balance", "icon_custom_emoji_id": "6111799373434197692", "style": "success"}
            ],
            [
                {"text": "Withdraw", "icon_custom_emoji_id": "6111799373434197692", "style": "primary"}, 
                {"text": "My Referrals", "icon_custom_emoji_id": "6109561463544747928", "style": "success"}
            ],
            [
                {"text": "Support", "icon_custom_emoji_id": "5337302974806922068", "style": "primary"}, 
                {"text": "New User", "icon_custom_emoji_id": "5352861489541714456", "style": "primary"}
            ]
        ],
        "resize_keyboard": True
    }

def getTasksMenu():
    return {
        "keyboard": [
            [{"text": "Instagram Work", "icon_custom_emoji_id": "6109335711473734674", "style": "primary"}],
            [{"text": "Facebook Work", "icon_custom_emoji_id": "6111896830537111232", "style": "primary"}],
            [{"text": "Cancel", "icon_custom_emoji_id": "6311965254817423602", "style": "danger"}]
        ],
        "resize_keyboard": True
    }

def getIgTasksMenu():
    return {
        "keyboard": [
            [{"text": f"Instagram 2FA (৳{rates['ig_2fa']:.2f})", "icon_custom_emoji_id": "6111799373434197692", "style": "success"}],
            [{"text": "Back", "icon_custom_emoji_id": "6109360506319935223", "style": "primary"}]
        ],
        "resize_keyboard": True
    }

def getFbTasksMenu():
    return {
        "keyboard": [
            [{"text": f"FB Cookies (৳{rates['fb_cookies']:.2f})", "icon_custom_emoji_id": "6111799373434197692", "style": "success"}],
            [{"text": "Back", "icon_custom_emoji_id": "6109360506319935223", "style": "primary"}]
        ],
        "resize_keyboard": True
    }

def getIgActionMenu():
    return {
        "keyboard": [
            [{"text": "Set 2FA", "icon_custom_emoji_id": "5353022963132174959", "style": "success"}],
            [{"text": "❓ How to work", "icon_custom_emoji_id": "5337302974806922068", "style": "primary"}],
            [{"text": "Cancel", "icon_custom_emoji_id": "6311965254817423602", "style": "danger"}]
        ],
        "resize_keyboard": True
    }

def getFbActionMenu():
    return {
        "keyboard": [
            [{"text": "Send UID", "icon_custom_emoji_id": "5353001161878182134", "style": "success"}],
            [{"text": "❓ How to work", "icon_custom_emoji_id": "5337302974806922068", "style": "primary"}],
            [{"text": "Cancel", "icon_custom_emoji_id": "6311965254817423602", "style": "danger"}]
        ],
        "resize_keyboard": True
    }

def getDoneMenu():
    return {
        "keyboard": [
            [{"text": "Account Done", "icon_custom_emoji_id": "6111726981760423576", "style": "success"}],
            [{"text": "Cancel", "icon_custom_emoji_id": "6311965254817423602", "style": "danger"}]
        ],
        "resize_keyboard": True
    }

def getCancelMenu():
    return {
        "keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "6311965254817423602", "style": "danger"}]],
        "resize_keyboard": True
    }

def getAdminMenu(chat_id):
    kb = [
        [{"text": "Users List", "icon_custom_emoji_id": "5352861489541714456", "callback_data": "admin_users", "style": "primary"}, 
         {"text": "Broadcast", "icon_custom_emoji_id": "5337302974806922068", "callback_data": "admin_broadcast", "style": "success"}],
        [{"text": "Approve IG", "icon_custom_emoji_id": "6111726981760423576", "callback_data": "admin_approve_ig", "style": "success"}, 
         {"text": "Approve FB", "icon_custom_emoji_id": "6111726981760423576", "callback_data": "admin_approve_fb", "style": "success"}],
        [{"text": "Export IG", "icon_custom_emoji_id": "5352721946054268944", "callback_data": "admin_export_ig", "style": "primary"}, 
         {"text": "Export FB", "icon_custom_emoji_id": "5352721946054268944", "callback_data": "admin_export_fb", "style": "primary"}],
        [{"text": "Set Rates", "icon_custom_emoji_id": "5420155432272438703", "callback_data": "admin_set_rates", "style": "primary"}, 
         {"text": "Support URL", "icon_custom_emoji_id": "5337302974806922068", "callback_data": "admin_set_support", "style": "primary"}],
        [{"text": "Withdraw Methods", "icon_custom_emoji_id": "6111799373434197692", "callback_data": "admin_withdraw_methods", "style": "primary"}, 
         {"text": "New User Guide", "icon_custom_emoji_id": "5353027129250453493", "callback_data": "admin_set_guide", "style": "primary"}],
        # NEW: Configurable guides for FB and IG
        [{"text": "Set IG Guide", "icon_custom_emoji_id": "6109432142079466939", "callback_data": "admin_set_ig_guide", "style": "primary"}, 
         {"text": "Set FB Guide", "icon_custom_emoji_id": "6109432142079466939", "callback_data": "admin_set_fb_guide", "style": "primary"}],
        [{"text": "Referral Settings", "icon_custom_emoji_id": "6109561463544747928", "callback_data": "admin_ref_settings", "style": "success"},
         {"text": "Force Sub", "icon_custom_emoji_id": "6260265754222924781", "callback_data": "admin_set_channel", "style": "primary"}],
        [{"text": "Download DB", "icon_custom_emoji_id": "5352721946054268944", "callback_data": "admin_download_db", "style": "primary"},
         {"text": "Upload DB", "icon_custom_emoji_id": "5352721946054268944", "callback_data": "admin_upload_db", "style": "primary"}]
    ]
    if str(chat_id) == str(ADMIN_ID):
        kb.append([{"text": "Manage Admins", "icon_custom_emoji_id": "5353032893096567467", "callback_data": "owner_manage_admins", "style": "danger"}])
    return {"inline_keyboard": kb}

# --- Handlers ---
def process_submission(chat_id, username, submission_text):
    task = user_current_task.get(chat_id)
    if task:
        submissions.append({
            "id": str(uuid.uuid4())[:8],
            "userId": chat_id,
            "username": username,
            "platform": task["platform"],
            "providedDetails": task["providedDetails"],
            "userSubmission": submission_text,
            "status": "pending",
            "reward": task["reward"],
            "submittedAt": time.time()
        })
        del user_current_task[chat_id]
        save_db()

def handle_message(msg):
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id: return
    text = msg.get("text", "")
    username = msg.get("from", {}).get("username", "")
    first_name = msg.get("from", {}).get("first_name", "")
    
    referrer_id = None
    if text.startswith("/start ") and len(text.split()) > 1:
        referrer_id = text.split()[1]

    init_user(chat_id, username, first_name, referrer_id)
    state = user_states.get(chat_id, "main")

    if text.startswith("/start"):
        user_states[chat_id] = "main"
        if not check_force_sub(chat_id):
            ask_force_sub(chat_id)
            return
        send_message(chat_id, f"{PEM['hi']} <b>Welcome to AdityaXwork!</b>\nSelect an option from the menu:", reply_markup=getMainMenu())
        return

    if not check_force_sub(chat_id):
        ask_force_sub(chat_id)
        return

    if text == "/admin":
        if is_admin(chat_id):
            send_message(chat_id, f"{PEM['admin']} <b>Admin Panel</b>", reply_markup=getAdminMenu(chat_id))
        return

    if text == "Cancel":
        if chat_id in user_current_task:
            del user_current_task[chat_id]
        send_message(chat_id, f"{PEM['no']} Cancelled.", reply_markup=getMainMenu())
        user_states[chat_id] = "main"
        return

    # Dynamic "How to work" button handler
    if text in ["❓ How to work", "❓ কিভাবে কাজ করব"]:
        task = user_current_task.get(chat_id)
        if not task:
            send_message(chat_id, f"{PEM['no']} Please select a work task first.", reply_markup=getMainMenu())
            return
        
        # Decide which guide to send based on current platform
        guide_key = "igGuide" if task["platform"] == "Instagram 2FA" else "fbGuide"
        guide = admin_settings.get(guide_key, {})
        gtype = guide.get("type", "text")
        fileId = guide.get("fileId", "")
        caption = guide.get("caption", "")
        
        # Keep the relevant action menu open
        rm = getIgActionMenu() if task["platform"] == "Instagram 2FA" else getFbActionMenu()
        
        if gtype == "text":
            send_message(chat_id, guide.get("text", "Guide not set."), reply_markup=rm)
        elif gtype == "photo":
            api_call("sendPhoto", {"chat_id": chat_id, "photo": fileId, "caption": caption, "parse_mode": "HTML", "reply_markup": rm})
        elif gtype == "video":
            api_call("sendVideo", {"chat_id": chat_id, "video": fileId, "caption": caption, "parse_mode": "HTML", "reply_markup": rm})
        elif gtype == "audio":
            api_call("sendAudio", {"chat_id": chat_id, "audio": fileId, "caption": caption, "parse_mode": "HTML", "reply_markup": rm})
        elif gtype == "voice":
            api_call("sendVoice", {"chat_id": chat_id, "voice": fileId, "caption": caption, "parse_mode": "HTML", "reply_markup": rm})
        elif gtype == "document":
            api_call("sendDocument", {"chat_id": chat_id, "document": fileId, "caption": caption, "parse_mode": "HTML", "reply_markup": rm})
        return

    # User States
    if state == "admin_awaiting_broadcast":
        success_count = 0
        for uid in users.keys():
            res = send_message(uid, f"{PEM['msg']} <b>Broadcast:</b>\n\n{text}")
            if res.get("ok"): success_count += 1
        send_message(chat_id, f"{PEM['ok']} Broadcast sent to {success_count} users.", reply_markup=getAdminMenu(chat_id))
        user_states[chat_id] = "main"
        return

    elif state.startswith("admin_awaiting_rate_"):
        ptype = state.split("_")[3]
        try:
            new_rate = float(text)
            if new_rate < 0: raise ValueError
            if ptype == "ig": rates["ig_2fa"] = new_rate
            if ptype == "fb": rates["fb_cookies"] = new_rate
            save_db()
            send_message(chat_id, f"{PEM['ok']} Rate updated to ৳{new_rate:.2f}.", reply_markup=getAdminMenu(chat_id))
            user_states[chat_id] = "main"
        except:
            send_message(chat_id, f"{PEM['no']} Invalid rate. Enter a valid number:")
        return

    elif state == "admin_awaiting_support_url":
        admin_settings["supportUrl"] = text
        save_db()
        send_message(chat_id, f"{PEM['ok']} Support URL updated.", reply_markup=getAdminMenu(chat_id))
        user_states[chat_id] = "main"
        return

    elif state == "admin_awaiting_db":
        if "document" in msg:
            file_id = msg["document"]["file_id"]
            if download_file(file_id, DB_FILE):
                load_db()
                send_message(chat_id, f"{PEM['ok']} Database uploaded and loaded successfully.", reply_markup=getAdminMenu(chat_id))
            else:
                send_message(chat_id, f"{PEM['no']} Failed to download the database file.", reply_markup=getAdminMenu(chat_id))
        else:
            send_message(chat_id, f"{PEM['no']} Please send a document (database.json).", reply_markup=getAdminMenu(chat_id))
        user_states[chat_id] = "main"
        return

    # Shared handler logic for storing guide files/text
    elif state in ["admin_awaiting_guide", "admin_awaiting_ig_guide", "admin_awaiting_fb_guide"]:
        if state == "admin_awaiting_guide": guide_key = "newUserGuide"
        elif state == "admin_awaiting_ig_guide": guide_key = "igGuide"
        else: guide_key = "fbGuide"

        if "photo" in msg:
            admin_settings[guide_key] = {"type": "photo", "fileId": msg["photo"][-1]["file_id"], "caption": msg.get("caption", "")}
        elif "video" in msg:
            admin_settings[guide_key] = {"type": "video", "fileId": msg["video"]["file_id"], "caption": msg.get("caption", "")}
        elif "audio" in msg:
            admin_settings[guide_key] = {"type": "audio", "fileId": msg["audio"]["file_id"], "caption": msg.get("caption", "")}
        elif "voice" in msg:
            admin_settings[guide_key] = {"type": "voice", "fileId": msg["voice"]["file_id"], "caption": msg.get("caption", "")}
        elif "document" in msg:
            admin_settings[guide_key] = {"type": "document", "fileId": msg["document"]["file_id"], "caption": msg.get("caption", "")}
        else:
            admin_settings[guide_key] = {"type": "text", "text": text}
        save_db()
        send_message(chat_id, f"{PEM['ok']} The Guide setup is saved successfully.", reply_markup=getAdminMenu(chat_id))
        user_states[chat_id] = "main"
        return

    elif state == "admin_awaiting_ref_tasks":
        try:
            req = int(text)
            if req < 1: raise ValueError
            admin_settings["referralTasksRequired"] = req
            save_db()
            send_message(chat_id, f"{PEM['ok']} Required tasks updated to {req}.", reply_markup=getAdminMenu(chat_id))
            user_states[chat_id] = "main"
        except:
            send_message(chat_id, f"{PEM['no']} Invalid number. Enter again:")
        return

    elif state == "admin_awaiting_ref_bonus":
        try:
            amt = float(text)
            if amt < 0: raise ValueError
            admin_settings["referralBonusAmount"] = amt
            save_db()
            send_message(chat_id, f"{PEM['ok']} Referral bonus updated to ৳{amt:.2f}.", reply_markup=getAdminMenu(chat_id))
            user_states[chat_id] = "main"
        except:
            send_message(chat_id, f"{PEM['no']} Invalid amount. Enter again:")
        return

    elif state == "owner_awaiting_add_admin":
        if str(chat_id) == str(ADMIN_ID):
            try:
                new_admin = int(text)
                if "admins" not in admin_settings:
                    admin_settings["admins"] = []
                if new_admin not in admin_settings["admins"]:
                    admin_settings["admins"].append(new_admin)
                    save_db()
                    send_message(chat_id, f"{PEM['ok']} Added {new_admin} as an admin.", reply_markup=getAdminMenu(chat_id))
                else:
                    send_message(chat_id, f"{PEM['warn']} {new_admin} is already an admin.", reply_markup=getAdminMenu(chat_id))
            except ValueError:
                send_message(chat_id, f"{PEM['no']} Invalid User ID. Enter again:")
                return
        user_states[chat_id] = "main"
        return

    elif state == "owner_awaiting_remove_admin":
        if str(chat_id) == str(ADMIN_ID):
            try:
                rem_admin = int(text)
                if "admins" in admin_settings and rem_admin in admin_settings["admins"]:
                    admin_settings["admins"].remove(rem_admin)
                    save_db()
                    send_message(chat_id, f"{PEM['ok']} Removed {rem_admin} from admins.", reply_markup=getAdminMenu(chat_id))
                else:
                    send_message(chat_id, f"{PEM['warn']} {rem_admin} is not an admin.", reply_markup=getAdminMenu(chat_id))
            except ValueError:
                send_message(chat_id, f"{PEM['no']} Invalid User ID. Enter again:")
                return
        user_states[chat_id] = "main"
        return

    elif state == "admin_awaiting_channel":
        if text.lower() == "none":
            admin_settings["must_join_channel"] = ""
        else:
            admin_settings["must_join_channel"] = text if text.startswith("@") else f"@{text}"
        save_db()
        send_message(chat_id, f"{PEM['ok']} Must join channel updated.", reply_markup=getAdminMenu(chat_id))
        user_states[chat_id] = "main"
        return

    elif state == "admin_awaiting_withdraw_name":
        user_temp_data[chat_id] = {"withdrawName": text}
        send_message(chat_id, f"Enter minimum withdraw amount for {text}:")
        user_states[chat_id] = "admin_awaiting_withdraw_min"
        return

    elif state == "admin_awaiting_withdraw_min":
        try:
            min_amt = int(text)
            if min_amt < 0: raise ValueError
            name = user_temp_data[chat_id]["withdrawName"]
            admin_settings["withdrawMethods"].append({"name": name, "minAmount": min_amt})
            save_db()
            send_message(chat_id, f"{PEM['ok']} Added method {name} (Min: {min_amt}).", reply_markup=getAdminMenu(chat_id))
            user_states[chat_id] = "main"
        except:
            send_message(chat_id, f"{PEM['no']} Invalid amount. Enter again:")
        return

    elif state.startswith("admin_awaiting_appr_count_"):
        parts = state.split("_")
        target_uid = int(parts[4])
        platform = "Instagram 2FA" if parts[5] == "ig" else "FB Cookies"
        try:
            approve_count = int(text)
            if approve_count < 0: raise ValueError
            
            user_pending = [s for s in submissions if s["status"] == "pending" and s["userId"] == target_uid and s["platform"] == platform]
            if approve_count > len(user_pending):
                send_message(chat_id, f"{PEM['no']} User only has {len(user_pending)} pending tasks. Enter a valid number:")
                return
                
            reward_added = 0
            for i, sub in enumerate(user_pending):
                if i < approve_count:
                    sub["status"] = "approved"
                    reward_added += sub["reward"]
                else:
                    sub["status"] = "rejected"
            save_db()

            if target_uid in users:
                u = users[target_uid]
                u["balance"] += reward_added
                u["totalEarned"] += reward_added
                
                if u.get("referredBy") and not u.get("referralBonusPaid"):
                    total_appr = len([s for s in submissions if s["userId"] == target_uid and s["status"] == "approved"])
                    if total_appr >= admin_settings.get("referralTasksRequired", 5):
                        u["referralBonusPaid"] = True
                        ref_id = u["referredBy"]
                        if ref_id in users:
                            bonus = admin_settings.get("referralBonusAmount", 10.0)
                            users[ref_id]["balance"] += bonus
                            users[ref_id]["totalEarned"] += bonus
                            send_message(ref_id, f"{PEM['gift']} <b>Referral Bonus!</b>\nOne of your referrals completed {admin_settings.get('referralTasksRequired', 5)} tasks.\n{PEM['money']} Added <b>৳{bonus:.2f}</b> to your balance!")

                save_db()
                notify_txt = f"{PEM['bell']} <b>Task Review Update ({platform})</b>\nYour {len(user_pending)} tasks were reviewed.\n{PEM['ok']} Approved: {approve_count}\n{PEM['no']} Rejected: {len(user_pending)-approve_count}\n\n{PEM['money']} Added <b>৳{reward_added:.2f}</b> to your balance!"
                send_message(target_uid, notify_txt)
                
            send_message(chat_id, f"{PEM['ok']} Approved {approve_count} tasks for user {target_uid}.", reply_markup=getAdminMenu(chat_id))
            user_states[chat_id] = "main"
        except:
            send_message(chat_id, f"{PEM['no']} Invalid number. Enter again:")
        return

    elif state == "awaiting_withdraw_method":
        method = next((m for m in admin_settings["withdrawMethods"] if m["name"] == text), None)
        if not method:
            send_message(chat_id, f"{PEM['no']} Please select a valid method.")
            return
        user_temp_data[chat_id] = {"method": method}
        send_message(chat_id, f"Enter amount to withdraw (Minimum {method['minAmount']}):", reply_markup=getCancelMenu())
        user_states[chat_id] = "awaiting_withdraw_amount"
        return

    elif state == "awaiting_withdraw_amount":
        try:
            amt = int(text)
            method = user_temp_data.get(chat_id, {}).get("method")
            if not method or amt < method["minAmount"]:
                send_message(chat_id, f"{PEM['no']} Invalid amount (Min {method['minAmount'] if method else 0}):")
                return
            
            user = users[chat_id]
            if amt > user["balance"]:
                send_message(chat_id, f"{PEM['no']} Insufficient balance!", reply_markup=getMainMenu())
            else:
                users[chat_id]["balance"] -= amt
                save_db()
                send_message(chat_id, f"{PEM['ok']} Your {method['name']} withdrawal request has been received.", reply_markup=getMainMenu())
            user_states[chat_id] = "main"
        except:
            send_message(chat_id, f"{PEM['no']} Invalid amount.")
        return

    elif state == "awaiting_ig_2fa":
        cleanKey = text.replace(" ", "").upper()
        try:
            totp = pyotp.TOTP(cleanKey)
            _ = totp.now() # Test
            if chat_id in user_current_task:
                user_current_task[chat_id]["tempKey"] = cleanKey
            send_message(chat_id, "After creating the account, click the button below:", reply_markup=getDoneMenu())
            user_states[chat_id] = "awaiting_ig_account_done"
        except:
            send_message(chat_id, f"{PEM['warn']} Invalid 2FA Key! Please try again.", reply_markup=getCancelMenu())
        return

    elif state == "awaiting_ig_account_done":
        if text == "Account Done":
            task = user_current_task.get(chat_id)
            if task and "tempKey" in task:
                try:
                    totp = pyotp.TOTP(task["tempKey"])
                    token = totp.now()
                    send_message(chat_id, "Copy the code below:")
                    send_message(chat_id, f"<code>{token}</code>")
                    send_message(chat_id, f"{PEM['ok']} Your submission has been accepted.", reply_markup=getMainMenu())
                    process_submission(chat_id, username, task["tempKey"])
                except:
                    send_message(chat_id, f"{PEM['no']} Error generating OTP. Start again.", reply_markup=getMainMenu())
            else:
                send_message(chat_id, f"{PEM['no']} Error, start again.", reply_markup=getMainMenu())
            user_states[chat_id] = "main"
        return

    elif state == "awaiting_fb_uid":
        if not text.isdigit() or len(text) < 14 or len(text) > 16:
            send_message(chat_id, f"{PEM['warn']} Invalid UID! Please enter a valid 14-16 digit UID.", reply_markup=getCancelMenu())
            return
        if chat_id in user_current_task:
            user_current_task[chat_id]["tempUid"] = text
        send_message(chat_id, f"{PEM['cookie']} Now send your Facebook Cookies:", reply_markup=getCancelMenu())
        user_states[chat_id] = "awaiting_fb_cookies"
        return

    elif state == "awaiting_fb_cookies":
        if "c_user=" not in text and "sessionid=" not in text:
            send_message(chat_id, f"{PEM['warn']} Invalid Cookies! Please copy full correct cookies from browser.", reply_markup=getCancelMenu())
            return
        if chat_id in user_current_task:
            user_current_task[chat_id]["tempKey"] = text
        send_message(chat_id, f"{PEM['ok']} UID and Cookies received. Click 'Account Done' to complete.", reply_markup=getDoneMenu())
        user_states[chat_id] = "awaiting_fb_account_done"
        return

    elif state == "awaiting_fb_account_done":
        if text == "Account Done":
            task = user_current_task.get(chat_id)
            if task and "tempUid" in task and "tempKey" in task:
                combined = f"UID: {task['tempUid']}\nCookies: {task['tempKey']}"
                process_submission(chat_id, username, combined)
                send_message(chat_id, f"{PEM['ok']} Your submission has been accepted.", reply_markup=getMainMenu())
            else:
                send_message(chat_id, f"{PEM['no']} Error, start again.", reply_markup=getMainMenu())
            user_states[chat_id] = "main"
        return

    # Regular Menu Matches
    if text == "Work":
        send_message(chat_id, "Select:", reply_markup=getTasksMenu())
    elif text == "Balance":
        user = users[chat_id]
        pending = len([s for s in submissions if s["userId"] == chat_id and s["status"] == "pending"])
        approved = len([s for s in submissions if s["userId"] == chat_id and s["status"] == "approved"])
        txt = f"{PEM['money']} <b>Your Balance</b>\n\n{PEM['money']} Balance: {user['balance']:.2f} BDT\n{PEM['wait']} Pending: 0.00 BDT\n{PEM['earn']} Total Earned: {user['totalEarned']:.2f} BDT\n\n{PEM['ok']} Approved: {approved}\n{PEM['wait']} In Review: {pending}"
        send_message(chat_id, txt, reply_markup=getMainMenu())
    elif text == "Withdraw":
        if not admin_settings["withdrawMethods"]:
            send_message(chat_id, f"{PEM['no']} No withdraw methods available.", reply_markup=getMainMenu())
            return
        methods_kb = [[{"text": m["name"], "icon_custom_emoji_id": "6111799373434197692", "style": "primary"}] for m in admin_settings["withdrawMethods"]]
        methods_kb.append([{"text": "Cancel", "icon_custom_emoji_id": "6188343249791358585", "style": "danger"}])
        send_message(chat_id, "Select Withdraw Method:", reply_markup={"keyboard": methods_kb, "resize_keyboard": True})
        user_states[chat_id] = "awaiting_withdraw_method"
    elif text == "My Referrals":
        total_ref = len([u for u in users.values() if u.get("referredBy") == chat_id])
        paid_ref = len([u for u in users.values() if u.get("referredBy") == chat_id and u.get("referralBonusPaid")])
        
        msg = f"{PEM['gift']} <b>Your Referral Link:</b>\n<code>https://t.me/{bot_username}?start={chat_id}</code>\n\n"
        msg += f"{PEM['group']} Total Refers: <b>{total_ref}</b>\n"
        msg += f"{PEM['check']} Qualified Refers: <b>{paid_ref}</b>\n\n"
        msg += f"<i>Get ৳{admin_settings.get('referralBonusAmount', 10.0):.2f} when your referral completes {admin_settings.get('referralTasksRequired', 5)} tasks!</i>"
        send_message(chat_id, msg, reply_markup=getMainMenu())
    elif text == "Support":
        kb = {"inline_keyboard": [[{"text": "Support", "icon_custom_emoji_id": "5337302974806922068", "url": admin_settings["supportUrl"], "style": "success"}]]}
        send_message(chat_id, f"{PEM['msg']} Contact our support team:", reply_markup=kb)
    elif text == "New User":
        guide = admin_settings.get("newUserGuide", {})
        gtype = guide.get("type", "text")
        fileId = guide.get("fileId", "")
        caption = guide.get("caption", "")
        if gtype == "text":
            send_message(chat_id, guide.get("text", ""), reply_markup=getMainMenu())
        elif gtype == "photo":
            api_call("sendPhoto", {"chat_id": chat_id, "photo": fileId, "caption": caption, "parse_mode": "HTML", "reply_markup": getMainMenu()})
        elif gtype == "video":
            api_call("sendVideo", {"chat_id": chat_id, "video": fileId, "caption": caption, "parse_mode": "HTML", "reply_markup": getMainMenu()})
        elif gtype == "audio":
            api_call("sendAudio", {"chat_id": chat_id, "audio": fileId, "caption": caption, "parse_mode": "HTML", "reply_markup": getMainMenu()})
        elif gtype == "voice":
            api_call("sendVoice", {"chat_id": chat_id, "voice": fileId, "caption": caption, "parse_mode": "HTML", "reply_markup": getMainMenu()})
        elif gtype == "document":
            api_call("sendDocument", {"chat_id": chat_id, "document": fileId, "caption": caption, "parse_mode": "HTML", "reply_markup": getMainMenu()})
    elif text == "Instagram Work":
        send_message(chat_id, "Select:", reply_markup=getIgTasksMenu())
    elif text == f"Instagram 2FA (৳{rates['ig_2fa']:.2f})":
        igDetails = f"{PEM['user']} Username: <code>bgysharmaltg</code>\n{PEM['key']} Password: <code>abdta@16</code>"
        send_message(chat_id, f"{igDetails}\n\n{PEM['target']} Open an account using the details above. Then click Set 2FA {PEM['hi']}", reply_markup=getIgActionMenu())
        user_current_task[chat_id] = {"platform": "Instagram 2FA", "providedDetails": igDetails, "reward": rates['ig_2fa']}
    elif text == "Set 2FA":
        send_message(chat_id, f"{PEM['key']} Send the 2FA Key:", reply_markup=getCancelMenu())
        user_states[chat_id] = "awaiting_ig_2fa"
    elif text == "Facebook Work":
        send_message(chat_id, "Select:", reply_markup=getFbTasksMenu())
    elif text == f"FB Cookies (৳{rates['fb_cookies']:.2f})":
        fbDetails = f"{PEM['user']} First name: <code>Julia</code>\n{PEM['user']} Last name: <code>oliveira</code>\n{PEM['key']} Password: <code>abdta@16</code>"
        send_message(chat_id, f"{fbDetails}\n\n{PEM['target']} Open an account using the details above and click Send UID {PEM['hi']}", reply_markup=getFbActionMenu())
        user_current_task[chat_id] = {"platform": "FB Cookies", "providedDetails": fbDetails, "reward": rates['fb_cookies']}
    elif text == "Send UID":
        send_message(chat_id, f"{PEM['rocket']} Send the 14-16 digit UID of your Facebook account:", reply_markup=getCancelMenu())
        user_states[chat_id] = "awaiting_fb_uid"
    elif text == "Back":
        send_message(chat_id, "Select:", reply_markup=getTasksMenu())
    else:
        if state == "main" and not text.startswith("/"):
            send_message(chat_id, "Please select an option from the menu.", reply_markup=getMainMenu())

def handle_callback(call):
    chat_id = call.get("message", {}).get("chat", {}).get("id")
    msg_id = call.get("message", {}).get("message_id")
    data = call.get("data", "")
    
    if not chat_id:
        return

    if data == "check_sub":
        if check_force_sub(chat_id):
            delete_message(chat_id, msg_id)
            send_message(chat_id, f"{PEM['ok']} Thank you for joining!", reply_markup=getMainMenu())
            answer_callback(call["id"], "Verified!")
        else:
            answer_callback(call["id"], "You haven't joined yet!", show_alert=True)
        return

    if not is_admin(chat_id):
        answer_callback(call["id"], "Not authorized.", show_alert=True)
        return

    if data == "admin_users":
        send_message(chat_id, f"{PEM['user']} Total Users: <b>{len(users)}</b>")
        answer_callback(call["id"])
    elif data == "admin_broadcast":
        send_message(chat_id, f"{PEM['msg']} Enter the message you want to broadcast:")
        user_states[chat_id] = "admin_awaiting_broadcast"
        answer_callback(call["id"])
    elif data.startswith("admin_export_"):
        pf = "Instagram 2FA" if data == "admin_export_ig" else "FB Cookies"
        pending = [s for s in submissions if s["status"] == "pending" and s["platform"] == pf]
        if not pending:
            send_message(chat_id, f"{PEM['warn']} No pending tasks to export for {pf}.")
            answer_callback(call["id"])
            return
        
        filename = f"pending_{pf.replace(' ', '')}.csv"
        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["User ID", "Username", "Platform", "Bot Provided Details", "User Submission", "Submitted At"])
                for s in pending:
                    writer.writerow([s["userId"], s.get("username","N/A"), s["platform"], s["providedDetails"].replace("\n"," "), s["userSubmission"].replace("\n"," "), time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(s["submittedAt"]))])
            with open(filename, "rb") as f:
                requests.post(f"{BASE_URL}/sendDocument", data={"chat_id": chat_id}, files={"document": f})
            os.remove(filename)
        except Exception as e:
            send_message(chat_id, f"Error exporting: {e}")
        answer_callback(call["id"])
    elif data.startswith("admin_approve_"):
        pf = "Instagram 2FA" if data == "admin_approve_ig" else "FB Cookies"
        pending_by_user = {}
        for s in submissions:
            if s["status"] == "pending" and s["platform"] == pf:
                pending_by_user.setdefault(s["userId"], []).append(s)
        
        if not pending_by_user:
            send_message(chat_id, f"{PEM['ok']} No pending tasks for {pf}.")
            answer_callback(call["id"])
            return
            
        kb = []
        for uid, subs in pending_by_user.items():
            u = users.get(str(uid), {})
            name = u.get("first_name") or u.get("username") or str(uid)
            kb.append([{"text": f"User: {name} | Tasks: {len(subs)}", "callback_data": f"appr_u_{uid}_{'ig' if data=='admin_approve_ig' else 'fb'}", "icon_custom_emoji_id": "5352861489541714456", "style": "primary"}])
        send_message(chat_id, f"Select user to approve {pf} tasks:", reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])
    elif data.startswith("appr_u_"):
        parts = data.split("_")
        uid = int(parts[2])
        pf = "Instagram 2FA" if parts[3] == "ig" else "FB Cookies"
        pending_count = len([s for s in submissions if s["status"] == "pending" and s["userId"] == uid and s["platform"] == pf])
        send_message(chat_id, f"{PEM['user']} User ID: {uid} has {pending_count} pending {pf} tasks.\nHow many to approve? (Enter number)")
        user_states[chat_id] = f"admin_awaiting_appr_count_{uid}_{parts[3]}"
        answer_callback(call["id"])
    elif data == "admin_set_rates":
        kb = [
            [{"text": f"Instagram (Current: ৳{rates['ig_2fa']:.2f})", "callback_data": "rate_ig", "icon_custom_emoji_id": "5420155432272438703", "style": "primary"}],
            [{"text": f"Facebook (Current: ৳{rates['fb_cookies']:.2f})", "callback_data": "rate_fb", "icon_custom_emoji_id": "5420155432272438703", "style": "primary"}]
        ]
        send_message(chat_id, "Select task to change rate:", reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])
    elif data == "rate_ig":
        send_message(chat_id, "Enter new rate for Instagram 2FA:")
        user_states[chat_id] = "admin_awaiting_rate_ig"
        answer_callback(call["id"])
    elif data == "rate_fb":
        send_message(chat_id, "Enter new rate for Facebook Cookies:")
        user_states[chat_id] = "admin_awaiting_rate_fb"
        answer_callback(call["id"])
    elif data == "admin_set_support":
        send_message(chat_id, "Enter the new support URL:")
        user_states[chat_id] = "admin_awaiting_support_url"
        answer_callback(call["id"])
    elif data == "admin_ref_settings":
        kb = [
            [{"text": f"Tasks Req (Current: {admin_settings.get('referralTasksRequired', 5)})", "callback_data": "ref_set_tasks", "style": "primary", "icon_custom_emoji_id": "6109432142079466939"}],
            [{"text": f"Bonus Amt (Current: ৳{admin_settings.get('referralBonusAmount', 10.0):.2f})", "callback_data": "ref_set_bonus", "style": "primary", "icon_custom_emoji_id": "6111799373434197692"}],
            [{"text": "Back to Admin", "callback_data": "admin_back", "style": "success", "icon_custom_emoji_id": "5352597830089347330"}]
        ]
        send_message(chat_id, f"{PEM['gear']} <b>Referral Settings</b>", reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])
    elif data == "ref_set_tasks":
        send_message(chat_id, "Enter number of tasks required for referral bonus:")
        user_states[chat_id] = "admin_awaiting_ref_tasks"
        answer_callback(call["id"])
    elif data == "ref_set_bonus":
        send_message(chat_id, "Enter referral bonus amount (৳):")
        user_states[chat_id] = "admin_awaiting_ref_bonus"
        answer_callback(call["id"])
    elif data == "admin_back":
        send_message(chat_id, f"{PEM['admin']} <b>Admin Panel</b>", reply_markup=getAdminMenu(chat_id))
        answer_callback(call["id"])
    
    # NEW admin panel button handlers for FB and IG guides
    elif data == "admin_set_ig_guide":
        send_message(chat_id, "Send the message (text, photo, video, audio, voice, document) for the 'Instagram Work Guide':")
        user_states[chat_id] = "admin_awaiting_ig_guide"
        answer_callback(call["id"])
    elif data == "admin_set_fb_guide":
        send_message(chat_id, "Send the message (text, photo, video, audio, voice, document) for the 'Facebook Work Guide':")
        user_states[chat_id] = "admin_awaiting_fb_guide"
        answer_callback(call["id"])
        
    elif data == "admin_set_guide":
        send_message(chat_id, "Send the message (text, photo, video, audio, voice, document) for the 'New User Guide':")
        user_states[chat_id] = "admin_awaiting_guide"
        answer_callback(call["id"])
    elif data == "admin_set_channel":
        send_message(chat_id, "Enter the channel username (e.g. @mychannel) or send 'none' to disable:")
        user_states[chat_id] = "admin_awaiting_channel"
        answer_callback(call["id"])
    elif data == "admin_withdraw_methods":
        kb = [
            [{"text": "Add Method", "icon_custom_emoji_id": "6188038822509418008", "callback_data": "withdraw_add", "style": "success"}],
            [{"text": "Clear All Methods", "icon_custom_emoji_id": "6188343249791358585", "callback_data": "withdraw_clear", "style": "danger"}],
            [{"text": "View Methods", "icon_custom_emoji_id": "6188447235244562676", "callback_data": "withdraw_view", "style": "primary"}]
        ]
        send_message(chat_id, f"{PEM['view']} <b>Withdraw Methods Settings</b>", reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])
    elif data == "withdraw_add":
        send_message(chat_id, "Enter method name (e.g. bKash):")
        user_states[chat_id] = "admin_awaiting_withdraw_name"
        answer_callback(call["id"])
    elif data == "withdraw_clear":
        admin_settings["withdrawMethods"] = []
        save_db()
        send_message(chat_id, f"{PEM['ok']} All withdraw methods cleared.")
        answer_callback(call["id"])
    elif data == "withdraw_view":
        txt = "<b>Withdraw Methods:</b>\n"
        for m in admin_settings["withdrawMethods"]:
            txt += f"- {m['name']} (Min: {m['minAmount']})\n"
        send_message(chat_id, txt)
        answer_callback(call["id"])
    elif data == "admin_download_db":
        send_document(chat_id, DB_FILE)
        answer_callback(call["id"], "Database sent!")
    elif data == "admin_upload_db":
        send_message(chat_id, "Send the database.json file to upload.")
        user_states[chat_id] = "admin_awaiting_db"
        answer_callback(call["id"])
    elif data == "owner_manage_admins":
        if str(chat_id) != str(ADMIN_ID):
            answer_callback(call["id"], "Owner only.", show_alert=True)
            return
        kb = [
            [{"text": "Add Admin", "icon_custom_emoji_id": "6188038822509418008", "callback_data": "admin_add_admin", "style": "success"}],
            [{"text": "Remove Admin", "icon_custom_emoji_id": "6188343249791358585", "callback_data": "admin_remove_admin", "style": "danger"}],
            [{"text": "View Admins", "icon_custom_emoji_id": "6188447235244562676", "callback_data": "admin_view_admins", "style": "primary"}],
            [{"text": "Back to Admin", "icon_custom_emoji_id": "5352597830089347330", "callback_data": "admin_back", "style": "primary"}]
        ]
        send_message(chat_id, f"{PEM['crown']} <b>Manage Admins</b>\nHere you can add or remove admin access.", reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])
    elif data == "admin_add_admin":
        if str(chat_id) != str(ADMIN_ID): return answer_callback(call["id"], "Owner only.", show_alert=True)
        send_message(chat_id, "Enter the User ID of the new admin:")
        user_states[chat_id] = "owner_awaiting_add_admin"
        answer_callback(call["id"])
    elif data == "admin_remove_admin":
        if str(chat_id) != str(ADMIN_ID): return answer_callback(call["id"], "Owner only.", show_alert=True)
        send_message(chat_id, "Enter the User ID to remove from admins:")
        user_states[chat_id] = "owner_awaiting_remove_admin"
        answer_callback(call["id"])
    elif data == "admin_view_admins":
        if str(chat_id) != str(ADMIN_ID): return answer_callback(call["id"], "Owner only.", show_alert=True)
        admins = admin_settings.get("admins", [])
        if not admins:
            txt = "No extra admins added."
        else:
            txt = "<b>Current Admins:</b>\n"
            for a in admins:
                txt += f"- <code>{a}</code>\n"
        send_message(chat_id, txt)
        answer_callback(call["id"])
    else:
        answer_callback(call["id"])

def main():
    global bot_username
    load_db()
    res = api_call("getMe")
    if res.get("ok"):
        bot_username = res["result"].get("username", bot_username)
        print(f"Bot started successfully: @{bot_username}")
    else:
        print("Error connecting to bot API. Please check your TOKEN.")
        return

    offset = None
    while True:
        try:
            updates = api_call(f"getUpdates?timeout=50&offset={offset}")
            if updates and "result" in updates:
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update:
                        handle_message(update["message"])
                    elif "callback_query" in update:
                        handle_callback(update["callback_query"])
        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    main()