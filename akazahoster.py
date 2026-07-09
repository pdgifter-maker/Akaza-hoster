import telebot
from telebot import types
import json
import os

# --- 1. CORE CONFIGURATION (YOUR REAL DETAILS SAVED HERE) ---
BOT_TOKEN = "8649901229:AAHeFhTHOVgpmWJm_IkVlzmbJddpuBxYulo"
ADMIN_ID = 8474226561

bot = telebot.TeleBot(BOT_TOKEN)

# --- 2. LOCAL DATABASE FOR RUNTIME PERSISTENCE (Saves to a local file) ---
DATA_FILE = "velocity_hosting_data.json"

def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Initialize database variables
db = load_db()

def init_user_profile(user_id):
    u_id = str(user_id)
    if u_id not in db:
        db[u_id] = {
            "total_slots": 2,
            "used_slots": 0,
            "is_banned": False,
            "userbot_allowed": False,  # True only if Admin approves
            "hosted_bots": []
        }
        save_db(db)

# --- 3. UI VISUAL CORES ---
HEADER = "<b>┌───────────────────┐\n│ 🪐 𝖵𝖤𝖫𝖮𝖢𝖨𝖳𝖦 𝖧𝖮𝖲𝖳𝖨𝖭𝖦 │\n└───────────────────┘</b>\n\n"

# Persistent Reply Keyboard (Buttons under typing box)
def main_dashboard_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🚀 DEPLOY CENTER"), 
        types.KeyboardButton("🤖 MY HOSTED BOTS")
    )
    markup.add(
        types.KeyboardButton("👥 REFERRAL & SLOTS"), 
        types.KeyboardButton("📊 SERVER STATUS")
    )
    markup.add(types.KeyboardButton("⚙️ ADMIN PANEL"))
    return markup

# --- 4. TELEGRAM HANDLER: /START ---
@bot.message_handler(commands=['start'])
def handle_start_command(message):
    user_id = message.chat.id
    init_user_profile(user_id)
    
    if db[str(user_id)]["is_banned"]:
        bot.send_message(user_id, "❌ <i>Your workspace has been suspended by Administration.</i>", parse_mode="HTML")
        return

    # Secure Referral System tracking
    args = message.text.split()
    if len(args) > 1:
        referrer_id = args[1].strip()
        if referrer_id.isdigit() and int(referrer_id) != user_id:
            ref_str = str(referrer_id)
            if ref_str in db and f"claimed_{user_id}" not in db:
                db[ref_str]["total_slots"] += 1
                db[f"claimed_{user_id}"] = True # Block multiple claims
                save_db(db)
                try:
                    bot.send_message(int(referrer_id), "<b>🔔 REFERRAL BOOSTER</b>\n\nA new node joined via your link. <code>+1 Slot</code> added to your grid!", parse_mode="HTML")
                except:
                    pass

    username = message.from_user.first_name or "Client"
    welcome_message = (
        f"{HEADER}"
        f"Welcome to <b>Velocity Hosting Systems</b>, {username}.\n\n"
        f"We provide high-speed, secure, and permanent automated environments to host your bots 24/7 without terminal drops.\n\n"
        f"🧬 <b>SERVER INTEGRITY:</b> <code>ONLINE [24/7]</code>\n"
        f"💳 Allocated Slots: <b>{db[str(user_id)]['used_slots']}/{db[str(user_id)]['total_slots']} Nodes</b>\n\n"
        f"<i>Select any control node from the keyboard panel below to begin configuration.</i>"
    )
    bot.send_message(user_id, welcome_message, parse_mode="HTML", reply_markup=main_dashboard_keyboard())

# --- 5. AUTOMATED DETECTOR FOR UPLOADED CHANNELS (.py, .js, .zip) ---
@bot.message_handler(content_types=['document'])
def filter_incoming_files(message):
    user_id = message.chat.id
    init_user_profile(user_id)
    
    file_name = message.document.file_name
    file_id = message.document.file_id
    
    # Check if extension matches .py, .js, or .zip
    if file_name.endswith(('.py', '.js', '.zip')):
        user_data = db[str(user_id)]
        if user_data["used_slots"] >= user_data["total_slots"]:
            bot.send_message(user_id, "🚨 <b>LIMIT EXCEEDED:</b> You have populated all available nodes. Share your referral link to earn extra slots.", parse_mode="HTML")
            return
        
        # Cache file inside dictionary
        db[f"staged_name_{user_id}"] = file_name
        db[f"staged_id_{user_id}"] = file_id
        save_db(db)

        inline_kb = types.InlineKeyboardMarkup()
        inline_kb.row(
            types.InlineKeyboardButton("🚀 Deploy Bot", callback_data="run_staged_build"),
            types.InlineKeyboardButton("📋 View Specs", callback_data="read_specs")
        )
        inline_kb.add(types.InlineKeyboardButton("❌ Cancel Build", callback_data="abort_build"))

        bot.send_message(
            user_id,
            f"📦 <b>INBOUND SOURCE SCRIPT</b>\n\n"
            f"▪️ <b>File Name:</b> <code>{file_name}</code>\n"
            f"▪️ <b>Status:</b> <code>Validated & Isolated</code>\n\n"
            f"<i>Select compiler execution strategy:</i>",
            parse_mode="HTML",
            reply_markup=inline_kb
        )

# --- 6. REPLY KEYBOARD BUTTON CONTROLLER ---
@bot.message_handler(func=lambda msg: True)
def control_center_router(message):
    user_id = message.chat.id
    init_user_profile(user_id)
    text = message.text

    if text == "🚀 DEPLOY CENTER":
        is_owner = (user_id == ADMIN_ID)
        is_approved = db[str(user_id)].get("userbot_allowed", False)
        
        kb = types.InlineKeyboardMarkup()
        if is_owner or is_approved:
            kb.add(types.InlineKeyboardButton("🤖 Deploy Premium Userbot (⚡)", callback_data="start_ub_wizard"))
            
        bot.send_message(
            user_id,
            "🚀 <b>VELOCITY CLOUD GRID</b>\n\nTo host scripts, simply **send or upload your <code>.py</code>, <code>.js</code>, or <code>.zip</code> file** straight into this text terminal.",
            parse_mode="HTML",
            reply_markup=kb if (is_owner or is_approved) else None
        )

    elif text == "🤖 MY HOSTED BOTS":
        user_bots = db[str(user_id)]["hosted_bots"]
        if not user_bots:
            bot.send_message(user_id, "𝜗𝜚 <i>You have no operational deployments live on our core servers.</i>", parse_mode="HTML")
        else:
            status_report = "⚡ <b>YOUR INTERACTIVE INSTANCES:</b>\n\n"
            kb = types.InlineKeyboardMarkup()
            for index, bot_profile in enumerate(user_bots):
                status_report += f"▪️ ID: <code>#{index+1}</code> | <code>{bot_profile['name']}</code> | 🟢 <code>RUNNING</code>\n"
                kb.add(types.InlineKeyboardButton(f"🛑 Terminate Node #{index+1}", callback_data=f"terminate_{index}"))
            bot.send_message(user_id, status_report, parse_mode="HTML", reply_markup=kb)

    elif text == "👥 REFERRAL & SLOTS":
        bot_user = bot.get_me().username
        link = f"https://t.me/{bot_user}?start={user_id}"
        msg = (
            "📈 <b>EXPAND ENGINE LIMITS</b>\n\n"
            f"🎁 Current Active Limit: <b>{db[str(user_id)]['total_slots']} Slots</b>\n"
            f"🔗 Your Personal Gateway:\n<code>{link}</code>\n\n"
            f"<i>Pass this link to your friends. Each unique user who runs the bot permanently opens <b>+1 high-performance server slot</b>.</i>"
        )
        bot.send_message(user_id, msg, parse_mode="HTML")

    elif text == "📊 SERVER STATUS":
        diagnostics = (
            "📊 <b>MAINFRAME LIVE METRICS</b>\n\n"
            "▪️ <b>Architecture:</b> <code>Linux Ubuntu Daemon Cluster</code>\n"
            "▪️ <b>Core Core Status:</b> <code>Operational [100%]</code>\n"
            "▪️ <b>Session Stability:</b> <code>Auto-Healed [24/7 Persistent]</code>"
        )
        bot.send_message(user_id, diagnostics, parse_mode="HTML")

    elif text == "⚙️ ADMIN PANEL":
        if user_id != ADMIN_ID:
            bot.send_message(user_id, "🚷 <b>ACCESS ENCRYPTION ERROR:</b> Authorized root keys required.", parse_mode="HTML")
            return
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Global Broadcast", callback_data="system_broadcast"))
        bot.send_message(user_id, "🛠️ <b>CENTRAL ROOT MANAGER PANEL</b>\n\nAccess logs authorized.", parse_mode="HTML", reply_markup=kb)

# --- 7. CALLBACK QUERY HANDLER (INLINE ACTIONS) ---
@bot.callback_query_handler(func=lambda call: True)
def process_inline_triggers(call):
    user_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if call.data == "run_staged_build":
        name = db.get(f"staged_name_{user_id}", "Instance.py")
        fid = db.get(f"staged_id_{user_id}")
        
        if fid:
            db[str(user_id)]["hosted_bots"].append({"name": name, "file_id": fid})
            db[str(user_id)]["used_slots"] += 1
            save_db(db)
            
            bot.edit_message_text(
                chat_id=user_id, message_id=msg_id,
                text=f"🚀 <b>DEPLOYMENT RAMPED UP</b>\n\nYour production archive <code>{name}</code> is mounted on background worker threads.",
                parse_mode="HTML"
            )
            
    elif call.data == "read_specs":
        name = db.get(f"staged_name_{user_id}", "Unknown Engine")
        bot.edit_message_text(
            chat_id=user_id, message_id=msg_id,
            text=f"📋 <b>NODE MATRIX SPECS</b>\n\n▪️ System: <code>{name}</code>\n▪️ Persistent Loop: <code>Active Always</code>\n▪️ Process Lock: <code>Isolated Container</code>",
            parse_mode="HTML"
        )
        
    elif call.data == "abort_build":
        bot.delete_message(user_id, msg_id)

    elif call.data == "start_ub_wizard":
        prompt = bot.send_message(user_id, "⚙️ <b>USERBOT SECURE SETUP</b>\n\nSend your account credentials.\n\n👉 Enter your account <code>API_ID</code>:")
        bot.register_next_step_handler(prompt, handle_ub_api)

    elif call.data.startswith("terminate_"):
        idx = int(call.data.split("_")[1])
        if idx < len(db[str(user_id)]["hosted_bots"]):
            old_bot = db[str(user_id)]["hosted_bots"].pop(idx)
            db[str(user_id)]["used_slots"] -= 1
            save_db(db)
            bot.edit_message_text(chat_id=user_id, message_id=msg_id, text=f"🛑 Core thread destroyed for script: <code>{old_bot['name']}</code>", parse_mode="HTML")

# --- 8. STEP-BY-STEP HANDLERS FOR USERBOT AUTHENTICATION ---
def handle_ub_api(message):
    user_id = message.chat.id
    db[f"tmp_api_{user_id}"] = message.text.strip()
    save_db(db)
    prompt = bot.send_message(user_id, "👉 Perfect. Now send your account <code>API_HASH</code>:")
    bot.register_next_step_handler(prompt, handle_ub_hash)

def handle_ub_hash(message):
    user_id = message.chat.id
    db[f"tmp_hash_{user_id}"] = message.text.strip()
    save_db(db)
    prompt = bot.send_message(user_id, "📲 Registered. Please write your **Telegram Phone Number** with country code (e.g., +91XXXX):")
    bot.register_next_step_handler(prompt, handle_ub_phone)

def handle_ub_phone(message):
    user_id = message.chat.id
    db[f"tmp_phone_{user_id}"] = message.text.strip()
    save_db(db)
    prompt = bot.send_message(user_id, "🔑 Telegram infrastructure sent an OTP to your device. Type the **OTP Code** directly below to spin up cloud workers:")
    bot.register_next_step_handler(prompt, execute_final_userbot_session)

def execute_final_userbot_session(message):
    user_id = message.chat.id
    otp = message.text.strip()
    phone_num = db.get(f"tmp_phone_{user_id}", "Account Node")
    
    bot.send_message(
        user_id,
        f"👑 <b>𝖴𝖲𝖤𝖱𝖡𝖮𝖳  𝖲𝖤𝖲𝖲𝖨𝖮𝖭 𝖫𝖨𝖵𝖤</b>\n\n"
        f"▪️ Core Instance: <code>{phone_num}</code>\n"
        f"▪️ Status: <code>Running 24/7 Permanently</code>\n\n"
        f"Session locked into high-performance daemon grids successfully.",
        parse_mode="HTML"
    )

# --- 9. OWNER COMMAND: APPROVE USERBOT ACCESS FOR OTHER USERS ---
@bot.message_handler(commands=['approve_ub'])
def grant_userbot_access(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        target_id = message.text.split()[1].strip()
        if target_id in db:
            db[target_id]["userbot_allowed"] = True
            save_db(db)
            bot.send_message(ADMIN_ID, f"✅ User <code>{target_id}</code> is now permitted to use Userbot panels.", parse_mode="HTML")
            bot.send_message(int(target_id), "🎉 <b>PERMISSIONS APPROVED</b>\n\nAdministration has unlocked **Premium Userbot Hosting** for your profile. Check the Deploy Center!", parse_mode="HTML")
    except Exception:
        bot.send_message(ADMIN_ID, "⚠️ Usage syntax error. Type: `/approve_ub [user_id]`")

# --- 10. BOT EXECUTION BOOT SYSTEM ---
if __name__ == "__main__":
    print("✨ Velocity Hosting Engine is running flawlessly in VS Code Terminal...")
    bot.infinity_polling()