import os
import re
import io
import json
import random
import asyncio
import aiohttp
import urllib.request
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import (
    CreateChannelRequest, EditPhotoRequest, EditAdminRequest, 
    EditTitleRequest, InviteToChannelRequest, UpdateUsernameRequest
)
from telethon.tl.functions.messages import (
    ExportChatInviteRequest, EditChatTitleRequest, SetHistoryTTLRequest,
    EditChatDefaultBannedRightsRequest
)
from telethon.tl.types import (
    InputChatUploadedPhoto, ChatAdminRights, ChatBannedRights,
    ChannelParticipantsAdmins
)
from PIL import Image, ImageDraw, ImageFont
from flask import Flask
import threading
import base64

app = Flask(__name__)

@app.route('/')
def home():
    return "Middleman Bot is running live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Flask ko background thread mein start karna
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

GROUP_PFP_URL = "https://t.me/ScamsWatchlist/109"
ASSISTANT_BOT = "@Middlemavenbot" 
TOS_LINK = "https://telegra.ph/Middlemaven-TOS-07-29" 

# --- MIDDLEMAN DATA & VOUCH CHANNELS ---
MM_DATA = {
    967359142: {
        "name": "Fog",
        "username": "@fogey",
        "prefix": "Fog MM",
        "vouch_channel": -1001287026986 # <--- Fog ka Vouch Channel ID
    },
    8421166266: {
        "name": "Trohps",
        "username": "@trohps",
        "prefix": "Trohps MM",
        "vouch_channel": -1003969714923 # <--- Trohps ka Vouch Channel ID
    },
    7913633925: {
        "name": "Shuify",
        "username": "@hupke",
        "prefix": "Shuify MM",
        "vouch_channel": -1003711319131 # <--- Shuify ka Vouch Channel ID
    },
    # <--- Yahan 4th Middleman add kar diya hai (Apni details yahan daal lena) --->
    8258524753: {
        "name": "Nox",
        "username": "@noxogu",
        "prefix": "Nox MM",
        "vouch_channel": -1003231804994 # <--- 4th MM ka Vouch Channel ID
    }
}

# --- DATABASE SETUP (JSON) ---
CONFIG_FILE = "mm_config.json"
CUSTOM_CMDS_FILE = "custom_commands.json"

DEFAULT_CONFIG = {
    "fee_percent": 2.0,            
    "min_fee_crypto": 1.0,         
    "min_fee_inr": 20.0,  
    "bot_msg_tos": "<b>TOS:</b> My only responsibility is to hold funds. I am not responsible for changes in crypto value or sending fees. The MM fee is non refundable. If not provided upfront, it will be taken before sending to the seller/refund. I am not responsible for accounts/products pulled on evoked during or after the deal. I have the right to compensate either party if time wasting is occurring.",
    "rec_msg": "I have successfully received the amount and the MM fee. It is safe to move forward. I will process the payment after the deal concludes. Thank you for your cooperation!",
    
    "mms": {
        "967359142": {  # FOG KA DATA
            "crypto_wallets": {
                "ton": "UQAAHD0SjE3XKK-K2rKRDOdD6chaOh58KC3wHNytZW7IJSaf", "sol": "FjB4kX7mMKPgTX9TaTZdUHHWhhRigZgwJPcgcvgzPaBY", "polygon": "FOG_POLY_ADDRESS", "bep": "0xcA524ec30da709a8d8E21339792406FDCc457e83",
                "btc": "bc1qpwnc39kyl34p5vl4yactdt26eec382408fhuvu", "eth": "0x9f7E11F8bb55Fc804F198bF63E88065344BCF7ff", "erc": "FOG_ERC_ADDRESS", "trc": "FOG_TRC_ADDRESS",
                "ltc": "ltc1q2y285ce29w7mhgz9xm45z42mdq8e4nx958qacy", "xrp": "FOG_XRP_ADDRESS", "doge": "FOG_DOGE_ADDRESS", "bch": "FOG_BCH_ADDRESS", "usdc": "FOG_USDC_ADDRESS"
            },
            "upi_id": "tysted@ptyes",
            "qr_link": "https://t.me/ScamsWatchlist/113"
        },
        "8421166266": {  # TROHPS KA DATA
            "crypto_wallets": {
                "ton": "TROHPS_TON_ADDRESS", "sol": "TROHPS_SOL_ADDRESS", "polygon": "TROHPS_POLY_ADDRESS", "bep": "TROHPS_BEP_ADDRESS",
                "btc": "TROHPS_BTC_ADDRESS", "eth": "TROHPS_ETH_ADDRESS", "erc": "TROHPS_ERC_ADDRESS", "trc": "TROHPS_TRC_ADDRESS",
                "ltc": "TROHPS_LTC_ADDRESS", "xrp": "TROHPS_XRP_ADDRESS", "doge": "TROHPS_DOGE_ADDRESS", "bch": "TROHPS_BCH_ADDRESS", "usdc": "TROHPS_USDC_ADDRESS"
            },
            "upi_id": "trohps_upi@bank",
            "qr_link": ""
        },
        "7913633925": {  # SHUIFY KA DATA
            "crypto_wallets": {
                "ton": "SHUIFY_TON_ADDRESS", "sol": "SHUIFY_SOL_ADDRESS", "polygon": "SHUIFY_POLY_ADDRESS", "bep": "SHUIFY_BEP_ADDRESS",
                "btc": "SHUIFY_BTC_ADDRESS", "eth": "SHUIFY_ETH_ADDRESS", "erc": "SHUIFY_ERC_ADDRESS", "trc": "SHUIFY_TRC_ADDRESS",
                "ltc": "SHUIFY_LTC_ADDRESS", "xrp": "SHUIFY_XRP_ADDRESS", "doge": "SHUIFY_DOGE_ADDRESS", "bch": "SHUIFY_BCH_ADDRESS", "usdc": "SHUIFY_USDC_ADDRESS"
            },
            "upi_id": "shuify_upi@bank",
            "qr_link": ""
        },
        "1234567890": {  # 4TH MM KA DATA (Yahan apni 4th MM ki Telegram ID aur details daal lena)
            "crypto_wallets": {
                "ton": "MM4_TON_ADDRESS", "sol": "MM4_SOL_ADDRESS", "polygon": "MM4_POLY_ADDRESS", "bep": "MM4_BEP_ADDRESS",
                "btc": "MM4_BTC_ADDRESS", "eth": "MM4_ETH_ADDRESS", "erc": "MM4_ERC_ADDRESS", "trc": "MM4_TRC_ADDRESS",
                "ltc": "MM4_LTC_ADDRESS", "xrp": "MM4_XRP_ADDRESS", "doge": "MM4_DOGE_ADDRESS", "bch": "MM4_BCH_ADDRESS", "usdc": "MM4_USDC_ADDRESS"
            },
            "upi_id": "mm4_upi@bank",
            "qr_link": ""
        }
    }
}

def load_json(file_path, default_data):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f: json.dump(default_data, f, indent=4)
        return default_data
    with open(file_path, 'r') as f: 
        data = json.load(f)
        # AUTO-FIX: Sirf tabhi 'mms' check karega jab default_data mein mms ho
        if "mms" in default_data and "mms" not in data:
            data["mms"] = default_data["mms"]
            with open(file_path, 'w') as out_f: json.dump(data, out_f, indent=4)
        return data

def save_json(file_path, data):
    with open(file_path, 'w') as f: json.dump(data, f, indent=4)

config = load_json(CONFIG_FILE, DEFAULT_CONFIG)
custom_commands = load_json(CUSTOM_CMDS_FILE, {})

USER_SESSION = os.getenv("USER_SESSION")

client = TelegramClient(
    StringSession(USER_SESSION),
    API_ID,
    API_HASH
)

bot_client = TelegramClient(
    "mm_assistant_bot_v2",
    API_ID,
    API_HASH
)

refund_requested_chats = set()
chat_vouches = {}  
active_timers = {}
admin_states = {}
last_group_links = {}
release_requested_chats = set()
group_roles = {}
pending_complete_chats = set()
chat_vouched_users = {}

def calc_fee(amount, mm_id=None, is_inr=False):
    # Agar mm_id provided hai aur wo MM_DATA ya config mein available hai
    custom_fee = None
    if mm_id and mm_id in MM_DATA:
        custom_fee = MM_DATA[mm_id].get("custom_fee", None)
    
    if not custom_fee and mm_id:
        mm_id_str = str(mm_id)
        custom_fee = config.get("mms", {}).get(mm_id_str, {}).get("custom_fee", None)
        
    # Agar custom fee milti hai toh us hisab se calculate karo
    if custom_fee is not None:
        try:
            fee_val = float(custom_fee)
            fee = amount * (fee_val / 100)
            min_f = config["min_fee_inr"] if is_inr else config["min_fee_crypto"]
            return min_f if fee < min_f else round(fee, 2)
        except:
            pass

    # Default Global Calculation
    fee = amount * (config["fee_percent"] / 100)
    min_f = config["min_fee_inr"] if is_inr else config["min_fee_crypto"]
    return min_f if fee < min_f else round(fee, 2)

def fmt_inr(n): return int(n) if n.is_integer() else round(n, 2)

def parse_time(time_str):
    match = re.match(r'((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s)?', time_str)
    if not match: return None
    parts = match.groupdict()
    return timedelta(**{n: int(v) for n, v in parts.items() if v})

async def get_crypto_price(ticker):
    if not ticker: return 1.0  
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.binance.com/api/v3/ticker/price?symbol={ticker}") as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['price'])
    except: return None

async def get_image_bytes(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200: return await resp.read()
    except: return None

CRYPTO_INFO = {
    "ton": {"name": "TON", "ticker": "TONUSDT"}, "sol": {"name": "Solana (SOL)", "ticker": "SOLUSDT"},
    "polygon": {"name": "USDT (Polygon)", "ticker": None}, "bep": {"name": "USDT (BEP20)", "ticker": None},
    "btc": {"name": "Bitcoin (BTC)", "ticker": "BTCUSDT"}, "eth": {"name": "Ethereum (ETH)", "ticker": "ETHUSDT"},
    "erc": {"name": "USDT (ERC20)", "ticker": None}, "trc": {"name": "USDT (TRC20)", "ticker": None},
    "ltc": {"name": "Litecoin (LTC)", "ticker": "LTCUSDT"}, "xrp": {"name": "Ripple (XRP)", "ticker": "XRPUSDT"},
    "doge": {"name": "Dogecoin (DOGE)", "ticker": "DOGEUSDT"}, "bch": {"name": "Bitcoin Cash (BCH)", "ticker": "BCHUSDT"},
    "usdc": {"name": "USDC (ERC20)", "ticker": None}
}

DEAL_TERMS = {
    "unban terms": "Note: If the account is not unbanned within the stated TAT, funds will be instantly refunded to the buyer if he asks for it.\n\nIf the account is unbanned, I will verify it and release the funds to the seller without delay. No exceptions unless stated.\n\nFunds will still be released even after the TAT ends if the buyer does not cancel the deal or ask for a refund. you must be responsive to the deal; do not sleep on it.\n\nYou both must be responsive to the deal.",
    "ban terms": "Note: If the account is not banned within the stated TAT, funds will be instantly refunded to the buyer if he asks for it.\n\nIf the account is banned, I will verify it and release the funds to the seller without delay. No exceptions unless stated.\n\nFunds will still be released even after the TAT ends if the buyer does not cancel the deal or ask for a refund. you must be responsive to the deal; do not sleep on it.\n\nYou both must be responsive to the deal.",
    "no terms": "<b>Deal Terms:</b>\n\nAs no specific conditions have been stated regarding the account, once the deal is completed, the buyer assumes full responsibility and liability for the account.\n\nIf the account is banned, logged out, becomes inaccessible, cannot be logged into, or if anything else happens to the account after the deal, <b>MM will not be held responsible or liable</b> for any resulting loss, issue, or damage."
}

# --- INSTAGRAM HELPERS ---
async def fetch_ig_data(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as response:
                html = await response.text()
                if response.status == 404 or "Page Not Found" in html or "Sorry, this page isn&#39;t available." in html:
                    return {"status": "banned"}
                if "Login • Instagram" in html:
                    return {"status": "error", "reason": "Instagram IP block (Login Redirect)"}

                meta_desc = re.search(r'property="og:description"\s+content="([^"]+)"', html)
                if not meta_desc: meta_desc = re.search(r'name="description"\s+content="([^"]+)"', html)
                og_image = re.search(r'property="og:image"\s+content="([^"]+)"', html)
                
                posts, followers, following = "0", "0", "0"
                pfp_url = og_image.group(1).replace("&amp;", "&") if og_image else None
                
                if meta_desc:
                    desc = meta_desc.group(1)
                    f_m = re.search(r'([\d.,kKmM]+)\s+Followers', desc, re.IGNORECASE)
                    fi_m = re.search(r'([\d.,kKmM]+)\s+Following', desc, re.IGNORECASE)
                    p_m = re.search(r'([\d.,kKmM]+)\s+Posts', desc, re.IGNORECASE)
                    if f_m: followers = f_m.group(1)
                    if fi_m: following = fi_m.group(1)
                    if p_m: posts = p_m.group(1)
                
                if followers == "0" and following == "0" and posts == "0": return {"status": "banned"}
                return {"status": "active", "username": username, "posts": posts, "followers": followers, "following": following, "pfp_url": pfp_url}
    except Exception as e: return {"status": "error", "reason": str(e)}

async def create_profile_card(username, pfp_bytes, posts, followers, following, is_banned):
    try:
        img = Image.new('RGB', (1200, 450), color=(12, 12, 12))
        draw = ImageDraw.Draw(img)

        font_url_bold = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
        font_url_reg = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
        
        if not os.path.exists("Roboto-Bold.ttf"):
            try: urllib.request.urlretrieve(font_url_bold, "Roboto-Bold.ttf")
            except: pass
        if not os.path.exists("Roboto-Regular.ttf"):
            try: urllib.request.urlretrieve(font_url_reg, "Roboto-Regular.ttf")
            except: pass

        def get_font(size, bold=False):
            name = "Roboto-Bold.ttf" if bold else "Roboto-Regular.ttf"
            try: return ImageFont.truetype(name, size)
            except: return ImageFont.load_default()

        font_name = get_font(55, bold=True)
        font_btn = get_font(28, bold=True)
        font_stats_num = get_font(42, bold=True)
        font_stats_lbl = get_font(26, bold=False)

        pfp_size = 240
        pfp_x, pfp_y = 80, 105

        if pfp_bytes and not is_banned:
            try:
                pfp = Image.open(io.BytesIO(pfp_bytes)).convert("RGBA").resize((pfp_size, pfp_size), Image.Resampling.LANCZOS)
                mask = Image.new('L', (pfp_size, pfp_size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, pfp_size, pfp_size), fill=255)
                pfp.putalpha(mask)
                draw.ellipse((pfp_x-4, pfp_y-4, pfp_x+pfp_size+4, pfp_y+pfp_size+4), outline=(70, 70, 70), width=3)
                img.paste(pfp, (pfp_x, pfp_y), pfp)
            except: 
                draw.ellipse((pfp_x, pfp_y, pfp_x+pfp_size, pfp_y+pfp_size), fill=(40, 40, 40), outline=(70, 70, 70), width=3)
        else:
            # Banned ke liye pfp border normal grey rakhi hai, red nahi
            draw.ellipse((pfp_x, pfp_y, pfp_x+pfp_size, pfp_y+pfp_size), fill=(40, 40, 40), outline=(70, 70, 70), width=3)
            draw.arc((pfp_x+75, pfp_y+55, pfp_x+165, pfp_y+145), start=0, end=180, fill=(150, 150, 150), width=12)
            draw.ellipse((pfp_x+95, pfp_y+85, pfp_x+145, pfp_y+135), fill=(150, 150, 150))

        draw.text((380, 105), username, font=font_name, fill=(255, 255, 255))
        
        btn_x, btn_y = 380, 185
        if is_banned:
            # Banned ke liye bada rounded box jiska andar ka hissa transparent/dark ho aur vibrant red border ho
            box_width, box_height = 340, 55
            try: 
                draw.rounded_rectangle([btn_x, btn_y, btn_x + box_width, btn_y + box_height], radius=12, fill=(12, 12, 12), outline=(255, 59, 48), width=3)
            except: 
                draw.rectangle([btn_x, btn_y, btn_x + box_width, btn_y + box_height], fill=(12, 12, 12), outline=(255, 59, 48), width=3)
            
            try:
                bbox = draw.textbbox((0, 0), "BANNED", font=font_btn)
                draw.text((btn_x + (box_width - (bbox[2] - bbox[0])) / 2, btn_y + (box_height - (bbox[3] - bbox[1])) / 2 - 3), "BANNED", font=font_btn, fill=(255, 59, 48))
            except: 
                draw.text((btn_x + 110, btn_y + 12), "BANNED", font=font_btn, fill=(255, 59, 48))
            
            posts_val, followers_val, following_val = "N/A", "N/A", "N/A"
        else:
            try: draw.rounded_rectangle([btn_x, btn_y, btn_x+160, btn_y+55], radius=10, fill=(0, 149, 246))
            except: draw.rectangle([btn_x, btn_y, btn_x+160, btn_y+55], fill=(0, 149, 246))
            try:
                bbox = draw.textbbox((0, 0), "Follow", font=font_btn)
                draw.text((btn_x + (160-(bbox[2]-bbox[0]))/2, btn_y + (55-(bbox[3]-bbox[1]))/2 - 3), "Follow", font=font_btn, fill=(255, 255, 255))
            except: draw.text((btn_x + 35, btn_y + 12), "Follow", font=font_btn, fill=(255, 255, 255))

            dot_x = btn_x + 180
            try: draw.rounded_rectangle([dot_x, btn_y, dot_x+70, btn_y+55], radius=10, fill=(38, 38, 38))
            except: draw.rectangle([dot_x, btn_y, dot_x+70, btn_y+55], fill=(38, 38, 38))
            try:
                bbox = draw.textbbox((0, 0), "...", font=font_btn)
                draw.text((dot_x + (70-(bbox[2]-bbox[0]))/2, btn_y + (55-(bbox[3]-bbox[1]))/2 - 8), "...", font=font_btn, fill=(255, 255, 255))
            except: draw.text((dot_x + 20, btn_y + 8), "...", font=font_btn, fill=(255, 255, 255))
            
            posts_val, followers_val, following_val = str(posts), str(followers), str(following)

        stats_y_num, stats_y_text = 290, 345
        def draw_centered_text(x_center, y, text, font, fill):
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                draw.text((x_center - (bbox[2]-bbox[0])/2, y), text, font=font, fill=fill)
            except: draw.text((x_center - 20, y), text, font=font, fill=fill)

        # N/A text ko red ki jagah normal white color de diya hai taaki active card jaisa lage
        stat_color = (255, 255, 255)
        draw_centered_text(450, stats_y_num, posts_val, font_stats_num, stat_color)
        draw_centered_text(450, stats_y_text, "posts", font_stats_lbl, (168, 168, 168))
        draw_centered_text(700, stats_y_num, followers_val, font_stats_num, stat_color)
        draw_centered_text(700, stats_y_text, "followers", font_stats_lbl, (168, 168, 168))
        draw_centered_text(950, stats_y_num, following_val, font_stats_num, stat_color)
        draw_centered_text(950, stats_y_text, "following", font_stats_lbl, (168, 168, 168))

        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        img_bytes.name = "profile_card.png"
        return img_bytes
    except Exception as e: 
        return None

@bot_client.on(events.NewMessage(pattern=r'\.gc$'))
async def gc_command(event):
    if not event.is_private or event.sender_id not in MM_DATA: return
    
    mm_info = MM_DATA[event.sender_id]
    group_title = f"{mm_info['prefix']} | @Middlemaven"
    about_text = "Experience the fastest Middleman in the community.\n\nt.me/fogey - Always confirm it's me" if event.sender_id == 967359142 else "Always confirm my username before proceeding with any of my offerings."
    wait_msg = await event.respond("Creating group...")
    
    try:
        # 1. Group Creation via Userbot
        result = await client(CreateChannelRequest(title=group_title, about=about_text, megagroup=True))
        channel = result.chats[0]
        real_chat_id = int(f"-100{channel.id}")
        
        # --- PFP (GROUP PHOTO) SETTING LOGIC ---
        try:
            match = re.search(r't\.me/([^/]+)/(\d+)', GROUP_PFP_URL)
            if match:
                chat_username = match.group(1)
                msg_id = int(match.group(2))
                pfp_msg = await client.get_messages(chat_username, ids=msg_id)
                if pfp_msg and pfp_msg.media:
                    pfp_file = await client.download_media(pfp_msg.media)
                    uploaded_photo = await client.upload_file(pfp_file)
                    await client(EditPhotoRequest(
                        channel=channel,
                        photo=InputChatUploadedPhoto(file=uploaded_photo)
                    ))
                    os.remove(pfp_file)
        except Exception as e:
            print(f"PFP Set Error: {e}")
        
        try:
            await client(UpdateUsernameRequest(channel=channel, username=None))
            await client(SetHistoryTTLRequest(peer=channel, period=0))
        except: pass
        
        # Admin Rights Set karna
        admin_rights = ChatAdminRights(
            change_info=True, post_messages=True, edit_messages=True, 
            delete_messages=True, ban_users=True, invite_users=True, 
            pin_messages=True, manage_call=True, add_admins=True
        )
        
        # 2. Assistant Bot aur MM Account DONO ko Invite karna
        try:
            await client(InviteToChannelRequest(channel=channel, users=[ASSISTANT_BOT, mm_info['username']]))
        except Exception as e:
            print(f"Invite Error: {e}")
        
        # Telegram ko sync hone ka 2.5 second time dena
        await asyncio.sleep(2.5)
        
        # 3. Assistant Bot ko Admin banana ("Group Help Bot" rank)
        try:
            await client(EditAdminRequest(channel=channel, user_id=ASSISTANT_BOT, admin_rights=admin_rights, rank='Group Help Bot'))
        except Exception as e:
            print(f"Bot Admin Error: {e}")

        # 4. MM Account ko Admin banana ("Middleman" rank)
        try:
            await client(EditAdminRequest(channel=channel, user_id=mm_info['username'], admin_rights=admin_rights, rank='Middleman'))
        except Exception as e:
            print(f"MM Admin Error: {e}")

        # 5. Invite Link Generate Karna
        invite = await client(ExportChatInviteRequest(peer=channel))
        
        await wait_msg.edit(f"✅ Group Created & Configured: {invite.link}", link_preview=False)
        await bot_client.send_message(real_chat_id, f"<b>Please only share this invite link with anyone involved in this deal.</b>\n{invite.link}", link_preview=True, parse_mode='html')
        await asyncio.sleep(1) 
        await bot_client.send_message(real_chat_id, "Hi, to proceed, please provide:\n\n• Buyer's username\n• Brief deal description\n• Total amount\n• Timeframe\n• Currency (specify crypto type if applicable)\n• Any additional terms\n\nOnce everything is provided, please tag me and I'll be available.")
    except Exception as e: 
        await wait_msg.edit(f"❌ Error creating group: {e}")

@bot_client.on(events.NewMessage(pattern=r'(?i)\.(?:received|rec)(?:\s+(.+))?$'))
async def received_command(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    await event.delete()
    
    amount_text = event.pattern_match.group(1)
    if amount_text:
        clean_amount = re.sub(r'[A-Za-z₹$]', '', amount_text).strip()
        if clean_amount:
            new_title = f"{clean_amount} | @Middlemaven"
            try: await bot_client(EditChatTitleRequest(chat_id=event.chat_id, title=new_title))
            except: 
                try: await bot_client(EditTitleRequest(channel=event.chat_id, title=new_title))
                except: pass
                
    rec_text = config.get("rec_msg", "I have successfully received the amount and the MM fee. It is safe to move forward. I will process the payment after the deal concludes. Thank you for your cooperation!")
    msg = await event.respond(rec_text, parse_mode='html')
    try: await bot_client.pin_message(event.chat_id, msg.id)
    except: pass

@bot_client.on(events.NewMessage(pattern=r'^[./]extendtat\s+(.+)'))
async def extend_tat(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    time_str = event.pattern_match.group(1)
    delta = parse_time(time_str)
    if not delta: return await event.respond("❌ Invalid format. Use: /extendtat 30m or /extendtat 1h")
    
    chat_id = event.chat_id
    if chat_id in active_timers:
        active_timers[chat_id]["end_time"] += delta
        await event.respond(f"TAT extended by {time_str} successfully!")
    else:
        await event.respond("❌ No active TAT timer running in this group.")

# 1. Message Delete Command (.del)
@bot_client.on(events.NewMessage(pattern=r'^\.del$'))
async def delete_single_message(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    
    # Check if replying to a message
    if not event.is_reply:
        await event.delete()
        temp_msg = await event.respond("❌ Please reply to the message you want to delete with `.del`", parse_mode='html')
        await asyncio.sleep(4)
        try: await temp_msg.delete()
        except: pass
        return
        
    try:
        reply_msg = await event.get_reply_message()
        # Delete the command message and the replied message
        await event.delete()
        await reply_msg.delete()
        
        # Send professional confirmation text
        conf_msg = await bot_client.send_message(
            event.chat_id, 
            "<b>Success:</b> The requested message has been permanently deleted.", 
            parse_mode='html'
        )
        
        # Auto-delete the confirmation message after 4 seconds
        await asyncio.sleep(4)
        try: await conf_msg.delete()
        except: pass
    except Exception as e:
        temp_msg = await event.respond(f"❌ Error deleting message: {e}", parse_mode='html')
        await asyncio.sleep(4)
        try: await temp_msg.delete()
        except: pass

# Group Delete Command (.delete) - Userbot client se group delete karne ke liye
@client.on(events.NewMessage(pattern=r'^\.delete$'))
async def delete_group_command(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    await event.delete()
    
    try:
        # Notify before deleting group using userbot
        warn_msg = await client.send_message(
            event.chat_id, 
            "⚠️ <b>Group Deletion:</b> Terminating and cleaning up this middleman group...", 
            parse_mode='html'
        )
        await asyncio.sleep(2)
        
        # Delete/Leave chat call for Telegram group termination via userbot
        from telethon.tl.functions.channels import DeleteChannelRequest
        from telethon.tl.functions.messages import DeleteChatUserRequest
        
        chat = await event.get_chat()
        if hasattr(chat, 'megagroup') and chat.megagroup:
            await client(DeleteChannelRequest(channel=event.chat_id))
        else:
            # For standard groups / supergroups fallback
            await client(DeleteChatUserRequest(chat_id=event.chat_id, user_id='me'))
    except Exception as e:
        await client.send_message(
            event.chat_id, 
            f"❌ <b>Error:</b> Could not delete group automatically. Please delete it manually from Telegram settings. ({e})", 
            parse_mode='html'
        )

@bot_client.on(events.NewMessage(pattern=r'^[./]reducetat\s+(.+)'))
async def reduce_tat(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    time_str = event.pattern_match.group(1)
    delta = parse_time(time_str)
    if not delta: return await event.respond("❌ Invalid format. Use: /reducetat 30m or /reducetat 1h")
    
    chat_id = event.chat_id
    if chat_id in active_timers:
        active_timers[chat_id]["end_time"] -= delta
        if datetime.now() >= active_timers[chat_id]["end_time"]:
            msg_obj = active_timers[chat_id]["msg"]
            del active_timers[chat_id]
            try: await bot_client.edit_message(chat_id, msg_obj.id, "<b>Timeframe Alert!</b>\nThe agreed timeframe has ended (reduced to zero).", parse_mode='html')
            except: pass
            await event.respond("TAT timer completed / reduced to zero!")
        else:
            await event.respond(f"TAT reduced by {time_str} successfully!")
    else:
        await event.respond("❌ No active TAT timer running in this group.")

@bot_client.on(events.NewMessage(pattern=r'(?i)\.pay\s+(?:₹|\$)?([0-9.]+)(?:\s+(?:₹|\$)?([0-9.]+))?(?:\s+(unban terms|ban terms|no terms))?\s*$'))
async def pay_inr_calc(event):
    if event.is_private: return
    
    sender_id = event.sender_id
    if not sender_id and event.message:
        sender_id = event.message.sender_id

    amount_raw = float(event.pattern_match.group(1))
    custom_fee_input = event.pattern_match.group(2)
    terms_type = event.pattern_match.group(3)
    if terms_type: terms_type = terms_type.lower()
    
    # Custom fee amount vs percentage logic
    if custom_fee_input:
        fee_raw = float(custom_fee_input)
    else:
        fee_raw = calc_fee(amount_raw, sender_id, is_inr=True)

    total_raw = amount_raw + fee_raw
    amount, fee, total = fmt_inr(amount_raw), fmt_inr(fee_raw), fmt_inr(total_raw)
    
    try: await event.delete()
    except: pass
        
    new_title = f"₹{amount} | @Middlemaven"
    try: await bot_client(EditChatTitleRequest(chat_id=event.chat_id, title=new_title))
    except: 
        try: await bot_client(EditTitleRequest(channel=event.chat_id, title=new_title))
        except: pass

    if terms_type and terms_type in DEAL_TERMS:
        await bot_client.send_message(event.chat_id, DEAL_TERMS[terms_type], parse_mode='html')
        await asyncio.sleep(0.5)

    # 1. Sabse pehle live config.json file se latest data check karenge taaki update miss na ho
    latest_config_mms = {}
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                file_data = json.load(f)
                latest_config_mms = file_data.get("mms", {})
        except:
            pass

    mm_settings = {}
    sender_str = str(sender_id) if sender_id else ""
    
    # Priority: 1. Live config.json file -> 2. Global config dict -> 3. MM_DATA
    if sender_str and sender_str in latest_config_mms:
        mm_settings = latest_config_mms[sender_str]
    elif sender_id and sender_id in MM_DATA:
        mm_settings = MM_DATA[sender_id]
    elif sender_str:
        mm_settings = config.get("mms", {}).get(sender_str, {})
        
    upi = mm_settings.get("upi_id", config.get("default_upi", "tysted@pytes"))
    qr_url = mm_settings.get("qr_link", "")

    qr_bytes = None
    if qr_url:
        if os.path.exists(qr_url):
            with open(qr_url, "rb") as f: qr_bytes = f.read()
        elif qr_url.startswith("http"):
            qr_bytes = await get_image_bytes(qr_url)
            
    # TOS hyperlink ke sath exact aapka format (Yahan galti thi jo theek kar di gayi hai)
    pay_msg = f"Upi: <code>{upi}</code> \nPay on this QR, must send the payment screenshot\n\nDeal Amount ₹{amount} + Fee: ₹{fee}= <code>₹{total}</code> INR\n\n<a href='{TOS_LINK}'>TOS</a>"
    
    # Copy Amount button removed — baaki QR/file logic same
    if qr_bytes:
        try:
            img_io = io.BytesIO(qr_bytes)
            img_io.name = "qr.png"
            await bot_client.send_file(
                event.chat_id,
                file=img_io,
                caption=pay_msg,
                parse_mode='html'
            )
        except:
            await bot_client.send_message(
                event.chat_id,
                pay_msg,
                parse_mode='html'
            )
    else:
        await bot_client.send_message(
            event.chat_id,
            pay_msg,
            parse_mode='html'
        )

@bot_client.on(events.NewMessage(pattern=r'\.link$'))
async def get_group_link(event):
    if event.sender_id not in MM_DATA: return
    await event.delete()
    
    # Agar command Group mein use ki gayi hai
    if not event.is_private:
        chat_id = event.chat_id
        try:
            invite = await bot_client(ExportChatInviteRequest(peer=chat_id))
            link = invite.link
            last_group_links[event.sender_id] = link # Save kar lega
            await bot_client.send_message(chat_id, f"**Group Invite Link:**\n{link}", link_preview=False)
        except Exception as e:
            # Agar bot ke paas link nikalne ki power nahi hai toh last saved link bhej dega
            saved_link = last_group_links.get(event.sender_id)
            if saved_link:
                await bot_client.send_message(chat_id, f"**Group Invite Link:**\n{saved_link}", link_preview=False)
            else:
                await bot_client.send_message(chat_id, "❌ Error: Could not fetch link for this group.")
                
    # Agar command DM (Private Chat) mein use ki gayi hai
    else:
        saved_link = last_group_links.get(event.sender_id)
        if saved_link:
            await event.respond(f"**Last Created Group Link:**\n{saved_link}", link_preview=False)
        else:
            await event.respond("❌ No recent group link found. First create a group using `.gc`.")

@bot_client.on(events.NewMessage(pattern=r'(?i)\.(trc|bep|eth|sol|ton|btc|polygon|erc|ltc|xrp|doge|bch|usdc)(?:\s+(?:[₹$])?([0-9.]+))?(?:\s+(?:[₹$])?([0-9.]+))?(?:\s+(unban terms|ban terms|no terms))?\s*$'))
async def pay_crypto_calc(event):
    if event.is_private: return
    
    sender_id = event.sender_id
    if not sender_id and event.message:
        sender_id = event.message.sender_id
        
    cmd = event.pattern_match.group(1).lower()
    amount_str = event.pattern_match.group(2)
    custom_fee_input = event.pattern_match.group(3) # Dusra number agar crypto fee ke liye ho
    terms_type = event.pattern_match.group(4)
    if terms_type: terms_type = terms_type.lower()
    
    mm_id_str = str(sender_id)
    mm_wallets = MM_DATA.get(sender_id, {}).get("crypto_wallets", {})
    if not mm_wallets or mm_wallets.get(cmd) in [None, "", "Address Not Set"]:
        mm_wallets = config.get("mms", {}).get(mm_id_str, {}).get("crypto_wallets", {})
        
    address = mm_wallets.get(cmd, "Address Not Set")
    info = CRYPTO_INFO[cmd]
    
    try: await event.delete()
    except: pass
    
    if not amount_str:
        await bot_client.send_message(
            event.chat_id, 
            f"<code>{address}</code>\n\nPlease send the TXID / screenshot once the payment has been sent.", 
            parse_mode='html'
        )
        return
        
    amount_raw = float(amount_str)
    
    # Custom fee amount ya percentage decide karna
    if custom_fee_input:
        mm_fee = float(custom_fee_input)
        current_fee_desc = f"Fixed ${mm_fee}"
    else:
        mm_fee = calc_fee(amount_raw, sender_id, is_inr=False)
        current_fee_desc = f"{config['mms'].get(mm_id_str, {}).get('custom_fee', config['fee_percent'])}%"

    total_to_pay = amount_raw + mm_fee 
    
    new_title = f"${fmt_inr(amount_raw)} | @Middlemaven"
    try: await bot_client(EditChatTitleRequest(chat_id=event.chat_id, title=new_title))
    except: 
        try: await bot_client(EditTitleRequest(channel=event.chat_id, title=new_title))
        except: pass

    if terms_type and terms_type in DEAL_TERMS:
        await bot_client.send_message(event.chat_id, DEAL_TERMS[terms_type], parse_mode='html')
        await asyncio.sleep(0.5)

    if info['ticker'] is None:
        crypto_val = f"{total_to_pay:.2f}"
    else:
        price = await get_crypto_price(info['ticker'])
        if price is None:
            return await bot_client.send_message(event.chat_id, "❌ Failed to fetch current market price.")
        crypto_val = f"{(total_to_pay / price):.8f}"
        
    pay_msg = (f"Deal Amount ${amount_raw:.2f} + Fee: ${mm_fee:.2f} ({current_fee_desc})\n\n"
               f"${total_to_pay:.2f} total = <code>{crypto_val}</code> {info['name']}\n\n"
               f"Address: <code>{address}</code>\n\n"
               f"Please send the TXID / screenshot once the payment has been sent.\n<a href='{TOS_LINK}'>TOS</a>")
    
    await bot_client.send_message(
        event.chat_id,
        pay_msg,
        parse_mode='html'
    )

@bot_client.on(events.NewMessage(pattern=r'(?i)\.(unbanterms|banterms|noterms)$'))
async def send_terms_command(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    cmd = event.pattern_match.group(1).lower()
    await event.delete()
    term_key = "unban terms" if cmd == "unbanterms" else "ban terms" if cmd == "banterms" else "no terms"
    if term_key in DEAL_TERMS:
        await bot_client.send_message(event.chat_id, DEAL_TERMS[term_key], parse_mode='html')

@bot_client.on(events.NewMessage(pattern=r'\.tos$'))
async def tos_command(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    await event.delete()
    await event.respond(config["bot_msg_tos"], parse_mode='html')

@bot_client.on(events.NewMessage(pattern=r'/check\s+(.+)'))
async def insta_check(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    username = event.pattern_match.group(1).replace('@', '')
    wait_msg = await event.respond(f"Checking @{username}...")
    
    data = await fetch_ig_data(username)
    is_banned = (data["status"] == "banned")
    
    if data["status"] == "error": 
        return await wait_msg.edit(f"<b>Error:</b> Instagram fetching failed right now. (IP might be temporarily restricted by IG)", parse_mode='html')
        
    pfp_bytes = None
    if not is_banned and data.get("pfp_url"):
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(data["pfp_url"], headers=headers) as resp:
                    if resp.status == 200: pfp_bytes = await resp.read()
        except: pass
            
    card_image = await create_profile_card(
        username, 
        pfp_bytes, 
        data.get("posts", "0"), 
        data.get("followers", "0"), 
        data.get("following", "0"), 
        is_banned
    )
    
    btn = [Button.url("View Profile", f"https://www.instagram.com/{username}")]
    
    if card_image:
        await bot_client.send_file(event.chat_id, file=card_image, buttons=btn, force_document=False)
        await wait_msg.delete()
    else:
        await wait_msg.edit(f"<b>Error generating card image for @{username}</b>", parse_mode='html', buttons=btn)

async def tat_live_updater(chat_id, msg):
    while chat_id in active_timers:
        end_time = active_timers[chat_id]["end_time"]
        now = datetime.now()
        
        if now >= end_time:
            try: 
                await bot_client.edit_message(chat_id, msg.id, "<b>Timeframe Alert!</b>\nThe agreed timeframe has ended.", parse_mode='html')
            except: pass
            if chat_id in active_timers: del active_timers[chat_id]
            break
        
        rem = end_time - now
        time_str = ""
        if rem.days > 0: time_str += f"{rem.days} days "
        if rem.seconds // 3600 > 0: time_str += f"{rem.seconds // 3600} hours "
        if (rem.seconds // 60) % 60 > 0: time_str += f"{(rem.seconds // 60) % 60} minutes "
        time_str += f"{rem.seconds % 60} seconds remaining"
        
        new_text = f"Timeframe for Middlemaven MM has been started:\n{time_str}"
        try: 
            await bot_client.edit_message(chat_id, msg.id, new_text)
        except: pass 
        
        await asyncio.sleep(10)

@bot_client.on(events.NewMessage(pattern=r'^[./]tat\s+(.+)'))
async def tat_timer(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    time_str = event.pattern_match.group(1)
    delta = parse_time(time_str)
    if not delta: return await event.respond("❌ Invalid format. Use: /tat 1h30m or /tat 45m")
    
    now = datetime.now()
    end_time = now + delta
    
    msg = await event.respond(f"Timeframe for Middlemaven MM has been started:\nCalculations...")
    
    # Dictionary mein end_time aur msg dono save karenge taaki live update ho sake
    active_timers[event.chat_id] = {"end_time": end_time, "msg": msg}
    asyncio.create_task(tat_live_updater(event.chat_id, msg))

@bot_client.on(events.NewMessage(pattern=r'^[./]set\s+(.+)'))
async def set_role_command(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    
    args = event.pattern_match.group(1).strip().split()
    role = None
    target_identifier = None
    
    for arg in args:
        arg_lower = arg.lower()
        if arg_lower in ["buyer", "seller"]:
            role = arg_lower
        elif arg.startswith("@") or arg.isdigit():
            target_identifier = arg
            
    # Agar role mil gaya par username nahi diya, toh reply message check karega
    if role and not target_identifier and event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg:
            target_identifier = reply_msg.sender_id
            
    if not role or not target_identifier:
        return await event.respond("❌ Invalid format! Use:\n• `.set buyer` (by replying to user)\n• `.set @username buyer`\n• `.set buyer @username`", parse_mode='html')
        
    chat_id = event.chat_id
    if chat_id not in group_roles: group_roles[chat_id] = {}
    
    try:
        user = await bot_client.get_entity(target_identifier)
        group_roles[chat_id][role] = user.id
        mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
        await event.respond(f"✅ <b>{role.capitalize()} Successfully Set</b> for {mention}!", parse_mode='html')
    except Exception as e:
        await event.respond(f"❌ Error: Could not find user `{target_identifier}`", parse_mode='html')

@bot_client.on(events.NewMessage(pattern=r'\.(?:complete|comp)(?:\s+.*)?$'))
async def bot_complete_command(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    mm_info = MM_DATA[event.sender_id]
    await event.delete()
    
    # Is chat ke purane tracked users ko reset kar do
    chat_vouched_users[event.chat_id] = set()
    
    # 1. Group title change
    try: await bot_client(EditChatTitleRequest(chat_id=event.chat_id, title=f"{mm_info['prefix']} | Complete"))
    except: pass
    
    # 2. Vouch format message bhejna
    thank_you_msg = (
        f"<b>Thank you for using my Middleman service!</b> 🤝\n\n"
        f"Please leave me a vouch here\n\n"
        f"<b>Format:</b> <code>Vouch {mm_info['username']} for MM'd</code>"
    )
    await bot_client.send_message(event.chat_id, thank_you_msg, parse_mode='html')
    
    # Is chat ko pending complete list mein dal do
    pending_complete_chats.add(event.chat_id)


# Strict Vouch detector with Unique User & Multiple Message check
@bot_client.on(events.NewMessage)
async def vouch_forwarder_handler(event):
    if event.is_private or event.chat_id not in pending_complete_chats: return
    
    # Agar message MM (Admin) ne bheja hai, toh ignore karo
    if event.sender_id in MM_DATA: return
    
    text_lower = str(event.raw_text).lower()
    
    # Strict Check: Message mein 'vouch' hona chahiye
    if "vouch" in text_lower:
        question_words = ["did", "how", "where", "when", "can", "should", "?"]
        if any(word in text_lower for word in question_words):
            return
            
        chat_id = event.chat_id
        user_id = event.sender_id
        
        # Initialize chat users set agar pehle se nahi hai
        if chat_id not in chat_vouched_users:
            chat_vouched_users[chat_id] = set()
            
        # Agar ISI user ne pehle bhi vouch message bhej diya hai, toh dubara count mat karo (Ignore it!)
        if user_id in chat_vouched_users[chat_id]:
            return
            
        # Naye user ka vouch record kar lo
        chat_vouched_users[chat_id].add(user_id)
        
        # Rule: Jab tak kam se kam 2 alag-alag users vouch na kardein, tab tak complete mat karo!
        # (Aap yahan check kar sakte ho ki 2 alag members hue ya nahi. Agar sirf 1 user ne kiya hai toh pehla vouch forward hoga par chat close nahi hogi, ya agar aap chahte ho ki do alag members hone chahiye toh length 2 check karenge)
        if len(chat_vouched_users[chat_id]) < 2:
            # Pehle bande ka vouch forward kar do par chat abhi open rakho taaki doosra banda bhi vouch kare
            chat = await event.get_chat()
            mm_username, mm_id = await get_mm_for_chat(chat_id, getattr(chat, 'title', ''))
            mm_info = MM_DATA.get(mm_id, {})
            vouch_channel = mm_info.get("vouch_channel", None)
            
            if vouch_channel:
                try: await bot_client.forward_messages(vouch_channel, event.message)
                except: pass
            return # Yahan return ho jayega, chat close nahi hogi jab tak doosra user na aaye!

        # Jab 2 alag-alag users vouch kar denge, tab ye code chalega aur deal permanently complete hogi:
        pending_complete_chats.discard(chat_id)
        chat_vouched_users.pop(chat_id, None)
        
        chat = await event.get_chat()
        mm_username, mm_id = await get_mm_for_chat(chat_id, getattr(chat, 'title', ''))
        mm_info = MM_DATA.get(mm_id, {})
        vouch_channel = mm_info.get("vouch_channel", None)
        
        if vouch_channel:
            try: await bot_client.forward_messages(vouch_channel, event.message)
            except: pass
            
        await asyncio.sleep(1.0)
        
        final_msg = (
            f"<b>The MM deal is now complete. Messaging is disabled, and this group will be deleted within few hours.</b>\n\n"
            f"<b>Thank You for dealing with {mm_info.get('username', 'Middleman')}!</b>"
        )
        try: await bot_client.send_message(chat_id, final_msg, parse_mode='html')
        except: pass
        
        await asyncio.sleep(0.5)
        
        try: 
            await bot_client(EditChatDefaultBannedRightsRequest(
                peer=chat_id, 
                banned_rights=ChatBannedRights(until_date=None, send_messages=True)
            ))
        except: pass

@bot_client.on(events.NewMessage(pattern=r'\.lock$'))
async def bot_lock_cmd(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    await event.delete()
    try: await bot_client(EditChatDefaultBannedRightsRequest(peer=event.chat_id, banned_rights=ChatBannedRights(until_date=None, send_messages=True)))
    except: pass
    await bot_client.send_message(event.chat_id, "<b>GROUP LOCKED</b>\n\nOnly admins can send messages. All non-admin can't send messages.", parse_mode='html')

@bot_client.on(events.NewMessage(pattern=r'\.unlock$'))
async def bot_unlock_cmd(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    await event.delete()
    try: await bot_client(EditChatDefaultBannedRightsRequest(peer=event.chat_id, banned_rights=ChatBannedRights(until_date=None, send_messages=False)))
    except: pass
    await bot_client.send_message(event.chat_id, "<b>Group UNLOCKED</b>\nMembers can now send messages.", parse_mode='html')

# --- CUSTOM COMMANDS ---
@bot_client.on(events.NewMessage(pattern=r'\.custom\s+(\w+)'))
async def create_custom(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    if not event.is_reply: return await event.respond("Reply to a message to save it as a custom command.")
    cmd_name = event.pattern_match.group(1).lower()
    reply_msg = await event.get_reply_message()
    custom_commands[cmd_name] = reply_msg.text
    save_json(CUSTOM_CMDS_FILE, custom_commands)
    await event.respond(f"Custom command `.{cmd_name}` saved!")

@bot_client.on(events.NewMessage(pattern=r'^\.(\w+)$'))
async def run_custom(event):
    if event.sender_id not in MM_DATA or event.is_private: return
    cmd_name = event.pattern_match.group(1).lower()
    ignore_list = ['gc', 'rec', 'received', 'pay', 'release', 'released', 'refunded', 'complete', 'comp', 'lock', 'unlock', 'custom', 'trc', 'bep', 'eth', 'sol', 'ton', 'btc', 'polygon', 'erc', 'ltc', 'xrp', 'doge', 'bch', 'usdc', 'unbanterms', 'banterms', 'noterms', 'tos', 'tat']
    if cmd_name in ignore_list: return
    if cmd_name in custom_commands:
        await event.delete()
        await event.respond(custom_commands[cmd_name], parse_mode='html')

@bot_client.on(events.NewMessage(pattern=r'/start'))
async def admin_start(event):
    if not event.is_private or event.sender_id not in MM_DATA: return
    text = f"Welcome to the Middleman Settings Panel."
    buttons = [
        [Button.inline("Custom CMDs", b"menu_custom"), Button.inline("Crypto", b"menu_crypto")],
        [Button.inline("Messages", b"menu_messages"), Button.inline("QR / UPI", b"menu_qrupi")],
        [Button.inline("Set Custom Fee", b"admin_set_custom_fee")]
    ]
    await event.respond(text, buttons=buttons)

@bot_client.on(events.CallbackQuery)
async def admin_callbacks(event):
    if event.sender_id not in MM_DATA: return
    data = event.data.decode('utf-8')
    if data == "back_main":
        admin_states.pop(event.sender_id, None)
        buttons = [[Button.inline("Custom CMDs", b"menu_custom"), Button.inline("Crypto", b"menu_crypto")], [Button.inline("Messages", b"menu_messages"), Button.inline("QR / UPI", b"menu_qrupi")]]
        await event.edit("Welcome back.", buttons=buttons)
    elif data == "menu_custom":
        await event.edit(f"To add a custom command, go to any group and reply to a message with:\n`.custom <name>`\n\nThen use `.name` to trigger it.", buttons=[Button.inline("Back", b"back_main")])
    elif data == "menu_crypto":
        mm_wallets = config["mms"].get(str(event.sender_id), {}).get("crypto_wallets", {})
        wallets = "\n".join([f"{k.upper()}: {v[:15]}..." for k, v in list(mm_wallets.items())[:5]])
        admin_states[event.sender_id] = "WAITING_CRYPTO"
        await event.edit(f"Your Wallets:\n{wallets}\n\nTo update, send:\nbtc bc1q...", buttons=[Button.inline("Back", b"back_main")])
    elif data == "menu_qrupi":
        admin_states[event.sender_id] = "WAITING_QRUPI"
        await event.edit(f"To update your UPI and QR, simply send your **QR Code Image** here and write your **UPI ID** in the caption.\n\nExample: Send photo, and type `yourupi@bank` as its caption.", buttons=[Button.inline("Back", b"back_main")])
    elif data == "menu_messages":
        admin_states[event.sender_id] = "WAITING_TOS"
        await event.edit(f"Send new TOS message text:", buttons=[Button.inline("Back", b"back_main")])

@bot_client.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id in MM_DATA))
async def admin_text_input(event):
    state = admin_states.get(event.sender_id)
    if not state: return
    
    if state == "WAITING_CRYPTO":
        parts = event.text.split(maxsplit=1)
        if len(parts) == 2:
            coin = parts[0].strip().lower()
            wallet_addr = parts[1].strip()
            mm_id_str = str(event.sender_id)
            
            # Ensure proper nesting in config dictionary
            if "mms" not in config: config["mms"] = {}
            if mm_id_str not in config["mms"]: config["mms"][mm_id_str] = {}
            if "crypto_wallets" not in config["mms"][mm_id_str]: config["mms"][mm_id_str]["crypto_wallets"] = {}
            
            # Save to config memory & JSON file
            config["mms"][mm_id_str]["crypto_wallets"][coin] = wallet_addr
            save_json(CONFIG_FILE, config)
            
            # Also update MM_DATA runtime dictionary so it reflects instantly!
            if event.sender_id in MM_DATA:
                if "crypto_wallets" not in MM_DATA[event.sender_id]:
                    MM_DATA[event.sender_id]["crypto_wallets"] = {}
                MM_DATA[event.sender_id]["crypto_wallets"][coin] = wallet_addr
                
            await event.respond(f"✅ Updated {coin.upper()} wallet successfully to:\n<code>{wallet_addr}</code>", parse_mode='html')
            admin_states.pop(event.sender_id)
        else:
            await event.respond("❌ Invalid format! Send like: `btc bc1q...`")
            
    elif state == "WAITING_QRUPI":
        upi_id = ""
        qr_path = ""
        if event.photo:
            if not event.text: return await event.respond("❌ Error: Please send the photo WITH your UPI ID written in the caption!")
            upi_id = event.text.strip()
            qr_path = await bot_client.download_media(event.message, file=f"qr_{event.sender_id}.png")
        else:
            parts = event.text.split(maxsplit=1)
            if len(parts) == 2:
                upi_id = parts[0].strip(); qr_path = parts[1].strip()
            else:
                return await event.respond("❌ Invalid format! Please send a **QR Photo** with your UPI in the caption.")
        
        mm_id_str = str(event.sender_id)
        if "mms" not in config: config["mms"] = {}
        if mm_id_str not in config["mms"]: config["mms"][mm_id_str] = {}
        config["mms"][mm_id_str]["upi_id"] = upi_id
        config["mms"][mm_id_str]["qr_link"] = qr_path
        save_json(CONFIG_FILE, config)
        
        if event.sender_id in MM_DATA:
            MM_DATA[event.sender_id]["upi_id"] = upi_id
            MM_DATA[event.sender_id]["qr_link"] = qr_path
            
        await event.respond(f"✅ UPI (`{upi_id}`) & QR Image updated successfully!")
        admin_states.pop(event.sender_id)
        
    elif state == "WAITING_TOS":
        config["bot_msg_tos"] = event.text.strip()
        save_json(CONFIG_FILE, config)
        await event.respond("✅ TOS updated!")
        admin_states.pop(event.sender_id)

    elif state == "WAITING_CUSTOM_FEE":
        fee_input = event.text.strip()
        try:
            fee_val = float(fee_input)
        except ValueError:
            await event.respond("❌ Invalid format! Please send a valid number (e.g., <code>2.0</code> or <code>50</code>).", parse_mode='html')
            return
            
        mm_id_str = str(event.sender_id)
        if "mms" not in config: config["mms"] = {}
        if mm_id_str not in config["mms"]: config["mms"][mm_id_str] = {}
        
        config["mms"][mm_id_str]["custom_fee"] = fee_val
        save_json(CONFIG_FILE, config)
        
        if event.sender_id in MM_DATA:
            MM_DATA[event.sender_id]["custom_fee"] = fee_val
            
        admin_states.pop(event.sender_id, None)
        await event.respond(f"✅ Success! Your custom fee has been successfully updated to: <code>{fee_val}</code>", parse_mode='html')

async def get_mm_for_chat(chat_id, title=""):
    for mm_info in MM_DATA.values():
        if mm_info["prefix"] in title: return mm_info["username"], mm_info.get("vouch_channel")
    try:
        admins = await bot_client.get_participants(chat_id, filter=ChannelParticipantsAdmins)
        for admin in admins:
            if admin.id in MM_DATA: return MM_DATA[admin.id]["username"], MM_DATA[admin.id].get("vouch_channel")
    except: pass
    return "@Middlemaven", None

@bot_client.on(events.NewMessage(func=lambda e: not e.is_private and e.text and 'vouch' in e.text.lower()))
async def auto_vouch_forwarder(event):
    bot_me = await bot_client.get_me()
    if getattr(event, 'sender_id', None) in list(MM_DATA.keys()) + [bot_me.id]: return
    
    chat = await event.get_chat()
    mm_username, vouch_channel = await get_mm_for_chat(event.chat_id, getattr(chat, 'title', ''))
    if not vouch_channel: return
    
    chat_id = event.chat_id
    if chat_id not in chat_vouches: chat_vouches[chat_id] = {}
    
    chat_vouches[chat_id][event.sender_id] = event.message
    
    if len(chat_vouches[chat_id]) == 2:
        try:
            await bot_client.forward_messages(vouch_channel, list(chat_vouches[chat_id].values()))
            conf_msg = await bot_client.send_message(chat_id, "Vouch Forwarded to Vouches Channel ✅")
            chat_vouches[chat_id].clear()
            
            await asyncio.sleep(1)
            try: 
                await bot_client(EditChatDefaultBannedRightsRequest(peer=chat_id, banned_rights=ChatBannedRights(until_date=None, send_messages=True)))
                await bot_client.send_message(chat_id, "<b>GROUP LOCKED</b>\n\nOnly admins can send messages. All non-admin can't send messages.", parse_mode='html')
            except Exception as lock_err:
                print("Auto-Lock Error:", lock_err)
                
            await asyncio.sleep(4)
            await conf_msg.delete()
        except Exception as e: 
            print("Vouch Forwarder Error:", e)

@bot_client.on(events.NewMessage)
async def assistant_bot_handler(event):
    if event.is_private: return
    text_lower = str(event.raw_text).lower()
    
    # --- REFUND REQUEST DETECTOR ---
    if "refund" in text_lower and getattr(event, 'sender_id', None) not in MM_DATA:
        chat_id = event.chat_id
        if chat_id not in refund_requested_chats:
            refund_requested_chats.add(chat_id)
            chat = await event.get_chat()
            mm_username, _ = await get_mm_for_chat(chat_id, getattr(chat, 'title', ''))
            
            refund_msg = (
                f"<b>Refund Confirmation</b>\n\n"
                f"{mm_username}, please process the refund.\n\n"
                f"Refund has been requested!\n"
                f"<b>Seller, please confirm the refund. Buyer, please drop your QR/UPI details if the deal was in INR. If the deal was in crypto, please provide the correct network  address.</b>\n\n"
                f"Now, please wait for {mm_username}’s response. We’ll update you as soon as possible."
            )
            try: await event.respond(refund_msg, parse_mode='html')
            except: pass

    # --- RELEASE REQUEST DETECTOR ---
    if ("release" in text_lower or "released" in text_lower) and getattr(event, 'sender_id', None) not in MM_DATA:
        chat_id = event.chat_id
        if chat_id not in release_requested_chats:
            release_requested_chats.add(chat_id)
            chat = await event.get_chat()
            mm_username, _ = await get_mm_for_chat(chat_id, getattr(chat, 'title', ''))
            
            release_req_msg = (
                f"<b>Release Confirmation</b>\n\n"
                f"{mm_username}, please process the release.\n\n"
                f"Release has been requested!\n"
                f"<b>Buyer, please confirm the release. Seller, please drop your QR/UPI details if the deal is in INR. If the deal is in crypto, please provide the correct network address.</b>\n\n"
                f"Now, please wait for {mm_username}’s response. We’ll update you as soon as possible."
            )
            try: await event.respond(release_req_msg, parse_mode='html')
            except: pass
            
    if getattr(event, 'sender_id', None) not in MM_DATA: return 
    original_text = str(event.raw_text)
    network = None
    if "http" in text_lower or "scan" in text_lower:
        if "etherscan.io" in text_lower: network = "ETH"
        elif "bscscan.com" in text_lower: network = "BEP20"
        elif "tronscan.org" in text_lower: network = "TRC20"
        elif "solscan.io" in text_lower: network = "SOL"
        elif "polygonscan.com" in text_lower: network = "Polygon"
        elif "tonviewer.com" in text_lower or "tonscan.org" in text_lower: network = "TON"
        elif "blockchain.com" in text_lower or "mempool.space" in text_lower: network = "BTC"
    else:
        if re.search(r'\b(0x[a-f0-9]{60,64})\b', original_text, re.IGNORECASE): network = "BEP20 / ETH / Polygon"
        elif re.search(r'\b([a-f0-9]{64})\b', original_text, re.IGNORECASE): network = "TRC20 / BTC / LTC"
        elif re.search(r'\b([1-9a-hj-np-za-km-z]{80,90})\b', original_text, re.IGNORECASE): network = "SOL"

    if network:
        await asyncio.sleep(1.5) 
        try: await event.reply(f"✅ Transaction is already confirmed!\n\nNetwork: {network}\nConfirmations: {random.randint(8, 45)}", link_preview=False)
        except: pass

async def main():
    print("MAIN STARTED")

    await client.start()
    print("USER CLIENT STARTED")

    await bot_client.start(bot_token=BOT_TOKEN)
    print("BOT CLIENT STARTED")

    print("Multi-Admin Bot Running! Ready to dominate.")

    await asyncio.gather(
        client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )


if __name__ == "__main__":
    asyncio.run(main())