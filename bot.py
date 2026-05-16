import telebot
from telebot import types
import requests
import time
from db import *

TOKEN = "8854612812:AAGCiJfGiyGFToo8WUimE2EVbR267g5rxOM"
ADMIN_ID = 123456789

API = "https://yourdomain.com/subapi.php?number="

CHANNELS = ["@channel1", "@channel2", "@channel3"]

bot = telebot.TeleBot(TOKEN)


# ================= FORCE JOIN =================
def check_join(uid):
    for ch in CHANNELS:
        try:
            m = bot.get_chat_member(ch, uid)
            if m.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True


# ================= START =================
@bot.message_handler(commands=['start'])
def start(m):

    uid = str(m.from_user.id)
    args = m.text.split()
    ref = args[1] if len(args) > 1 else None

    create_user(uid, m.from_user.first_name, ref)

    if not check_join(uid):

        btn = types.InlineKeyboardMarkup()

        for ch in CHANNELS:
            btn.add(types.InlineKeyboardButton(
                f"📢 Join {ch}",
                url=f"https://t.me/{ch.replace('@','')}"
            ))

        btn.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))

        bot.send_message(m.chat.id,
            "⚠️ <b>Join All Channels First</b>",
            parse_mode="HTML",
            reply_markup=btn)
        return

    menu(m.chat.id)


# ================= VERIFY =================
@bot.callback_query_handler(func=lambda c: c.data == "verify")
def verify(c):
    uid = str(c.from_user.id)

    if check_join(uid):
        bot.answer_callback_query(c.id, "Verified ✅")
        menu(c.message.chat.id)
    else:
        bot.answer_callback_query(c.id, "❌ Join All Channels")


# ================= MENU UI =================
def menu(chat_id):

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton("🔎 Lookup", callback_data="lk"),
        types.InlineKeyboardButton("👤 Profile", callback_data="pr")
    )

    kb.row(
        types.InlineKeyboardButton("🎁 Refer", callback_data="ref"),
        types.InlineKeyboardButton("🏆 Top", callback_data="top")
    )

    bot.send_message(chat_id,
        "✨ <b>PRO BOT READY</b>\n🚀 Fast • Secure • Stylish",
        parse_mode="HTML",
        reply_markup=kb)


# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: True)
def cb(c):

    uid = str(c.from_user.id)

    if not check_join(uid):
        bot.answer_callback_query(c.id, "Join Channels First")
        return

    # LOOKUP
    if c.data == "lk":
        msg = bot.send_message(c.message.chat.id, "🔎 Send Number:")
        bot.register_next_step_handler(msg, lookup)

    # PROFILE
    elif c.data == "pr":
        u = get_user(uid)
        bot.send_message(c.message.chat.id,
            f"👤 Name: {u[1]}\n💎 Points: {u[2]}")

    # REFER
    elif c.data == "ref":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(c.message.chat.id, f"🎁 Referral Link:\n{link}")

    # TOP
    elif c.data == "top":
        data = top_users()
        msg = "🏆 TOP USERS\n\n"
        for i, u in enumerate(data, 1):
            msg += f"{i}. {u[0]} - {u[1]}\n"
        bot.send_message(c.message.chat.id, msg)


# ================= ANIMATED LOOKUP =================
def lookup(m):

    uid = str(m.from_user.id)

    if is_banned(uid):
        bot.reply_to(m, "❌ Banned User")
        return

    u = get_user(uid)
    if u[2] <= 0:
        bot.reply_to(m, "❌ No Points")
        return

    number = m.text

    msg = bot.send_message(m.chat.id, "⚡ Searching")

    for i in range(4):
        time.sleep(0.4)
        bot.edit_message_text("⚡ Searching" + "." * i,
            m.chat.id, msg.message_id)

    try:
        data = requests.get(API + number).json()

        update_points(uid, u[2] - 1)

        bot.edit_message_text(f"""
╔════ RESULT ════╗
📛 Name: {data.get('name')}
📱 Number: {data.get('number')}
🌍 Country: {data.get('country')}
📡 Carrier: {data.get('carrier')}

💎 Left: {u[2]-1}
""", m.chat.id, msg.message_id)

    except:
        bot.edit_message_text("❌ API ERROR", m.chat.id, msg.message_id)


# ================= ADMIN PANEL =================
@bot.message_handler(commands=['admin'])
def admin(m):

    if m.from_user.id != ADMIN_ID:
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("📊 Stats", "📢 Broadcast")
    kb.row("➕ Add", "➖ Remove")
    kb.row("🚫 Ban", "✅ Unban")

    bot.send_message(m.chat.id, "🛠 ADMIN PANEL", reply_markup=kb)


# ================= ADMIN ACTIONS =================
@bot.message_handler(func=lambda m: m.text == "📊 Stats")
def st(m):
    if m.from_user.id == ADMIN_ID:
        u, p = stats()
        bot.reply_to(m, f"👥 Users: {u}\n💎 Points: {p}")


@bot.message_handler(func=lambda m: m.text == "📢 Broadcast")
def bc(m):
    if m.from_user.id != ADMIN_ID:
        return

    msg = bot.reply_to(m, "Send message")
    bot.register_next_step_handler(msg, send_all)


def send_all(m):
    users = all_users()
    c = 0
    for u in users:
        try:
            bot.send_message(u[0], m.text)
            c += 1
        except:
            pass
    bot.reply_to(m, f"✅ Sent {c}")


@bot.message_handler(func=lambda m: m.text == "➕ Add")
def add(m):
    msg = bot.reply_to(m, "user_id amount")
    bot.register_next_step_handler(msg, do_add)


def do_add(m):
    try:
        uid, amt = m.text.split()
        add_points(uid, int(amt))
        bot.reply_to(m, "✅ Added")
    except:
        bot.reply_to(m, "❌ Error")


@bot.message_handler(func=lambda m: m.text == "➖ Remove")
def rm(m):
    msg = bot.reply_to(m, "user_id amount")
    bot.register_next_step_handler(msg, do_rm)


def do_rm(m):
    try:
        uid, amt = m.text.split()
        add_points(uid, -int(amt))
        bot.reply_to(m, "✅ Removed")
    except:
        bot.reply_to(m, "❌ Error")


@bot.message_handler(func=lambda m: m.text == "🚫 Ban")
def ban(m):
    msg = bot.reply_to(m, "user_id")
    bot.register_next_step_handler(msg, lambda x: (ban_user(x.text), bot.reply_to(x, "🚫 Banned")))


@bot.message_handler(func=lambda m: m.text == "✅ Unban")
def unban(m):
    msg = bot.reply_to(m, "user_id")
    bot.register_next_step_handler(msg, lambda x: (unban_user(x.text), bot.reply_to(x, "✅ Unbanned")))


print("🚀 PRO BOT RUNNING...")
bot.infinity_polling(skip_pending=True)
