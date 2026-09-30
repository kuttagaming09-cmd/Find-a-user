import os
import json
import time
import hmac
import hashlib
import logging
import sqlite3
from threading import Thread, Lock

from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# ============================================================
# CONFIG
# ============================================================

# IMPORTANT:
# The old bot token was exposed in chat. Revoke it with @BotFather
# and put the NEW token here (or set BOT_TOKEN as an environment variable).
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_NEW_BOT_TOKEN_HERE")

# Replace with your numeric Telegram user ID.
ADMIN_CHAT_ID = 123456789

# Put your real HTTPS Mini App URL here.
MINI_APP_URL = "https://your-domain.com/index.html"

HOST = "0.0.0.0"
PORT = 5000

# Security database
DB_FILE = "security.db"

# If True, once an IP is assigned to one Telegram account,
# a different Telegram account using that IP is permanently banned.
BAN_ON_SECOND_ACCOUNT = True

# ============================================================
# LOGGING / APP
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

app = Flask(__name__)
telegram_bot = Bot(token=BOT_TOKEN)
db_lock = Lock()


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db_lock:
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ip_accounts (
                ip TEXT PRIMARY KEY,
                telegram_id TEXT NOT NULL,
                username TEXT,
                first_seen INTEGER NOT NULL,
                last_seen INTEGER NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS banned_ips (
                ip TEXT PRIMARY KEY,
                telegram_id TEXT,
                reason TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                telegram_id TEXT PRIMARY KEY,
                reason TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_txids (
                txid TEXT PRIMARY KEY,
                telegram_id TEXT,
                created_at INTEGER NOT NULL
            )
        """)

        conn.commit()
        conn.close()


# ============================================================
# CLIENT IP
# ============================================================

def get_client_ip():
    """
    Use the direct Flask peer IP by default.
    Do NOT blindly trust X-Forwarded-For because a client can spoof it.
    If you later put this behind a trusted reverse proxy, configure
    proxy handling separately.
    """
    return (request.remote_addr or "").strip() or "unknown"


# ============================================================
# TELEGRAM WEB APP INIT DATA VERIFICATION
# ============================================================

def verify_telegram_init_data(init_data: str):
    """
    Verifies Telegram Mini App initData according to Telegram's
    WebApp validation method.

    Returns:
        dict user data on success
        None on failure
    """
    if not init_data or BOT_TOKEN == "PUT_NEW_BOT_TOKEN_HERE":
        return None

    try:
        parsed = dict(
            item.split("=", 1)
            for item in init_data.split("&")
            if "=" in item
        )

        received_hash = parsed.pop("hash", None)
        auth_date = parsed.get("auth_date")

        if not received_hash or not auth_date:
            return None

        # Reject very old initData.
        if abs(int(time.time()) - int(auth_date)) > 86400:
            return None

        data_check_string = "\n".join(
            f"{key}={parsed[key]}"
            for key in sorted(parsed)
        )

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode("utf-8"),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        user_json = parsed.get("user")
        if not user_json:
            return None

        user = json.loads(user_json)

        if not user.get("id"):
            return None

        return user

    except Exception as e:
        logging.warning("Telegram initData verification failed: %s", e)
        return None


def get_verified_user():
    """
    Accept initData from JSON body or X-Telegram-Init-Data header.
    The Telegram user object sent separately by the browser is NOT trusted.
    """
    init_data = request.headers.get("X-Telegram-Init-Data", "")

    if not init_data:
        data = request.get_json(silent=True) or {}
        init_data = data.get("initData", "")

    return verify_telegram_init_data(init_data)


# ============================================================
# IP SECURITY
# ============================================================

def security_check(user):
    """
    One IP -> one Telegram account.

    First account:
        IP is registered.

    Same account from same IP:
        Allowed.

    Different account from same IP:
        Both the IP and the second Telegram account are banned.

    Returns:
        (True, None) when allowed
        (False, response_message) when blocked
    """
    ip = get_client_ip()
    telegram_id = str(user["id"])
    username = user.get("username", "")

    now = int(time.time())

    with db_lock:
        conn = get_db()

        # Existing IP ban
        banned_ip = conn.execute(
            "SELECT ip FROM banned_ips WHERE ip = ?",
            (ip,)
        ).fetchone()

        if banned_ip:
            conn.close()
            return False, {
                "success": False,
                "banned": True,
                "message": "This IP address is banned."
            }

        # Existing user ban
        banned_user = conn.execute(
            "SELECT telegram_id FROM banned_users WHERE telegram_id = ?",
            (telegram_id,)
        ).fetchone()

        if banned_user:
            conn.close()
            return False, {
                "success": False,
                "banned": True,
                "message": "This Telegram account is banned."
            }

        existing = conn.execute(
            "SELECT telegram_id FROM ip_accounts WHERE ip = ?",
            (ip,)
        ).fetchone()

        if existing:
            owner_id = str(existing["telegram_id"])

            if owner_id != telegram_id and BAN_ON_SECOND_ACCOUNT:
                reason = (
                    "Second Telegram account detected from the same IP. "
                    f"Original account: {owner_id}; second account: {telegram_id}"
                )

                conn.execute(
                    """
                    INSERT OR REPLACE INTO banned_ips
                    (ip, telegram_id, reason, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (ip, telegram_id, reason, now)
                )

                conn.execute(
                    """
                    INSERT OR REPLACE INTO banned_users
                    (telegram_id, reason, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (telegram_id, reason, now)
                )

                conn.commit()
                conn.close()

                logging.warning(
                    "SECURITY BAN: IP=%s original_user=%s second_user=%s",
                    ip, owner_id, telegram_id
                )

                return False, {
                    "success": False,
                    "banned": True,
                    "message": "Multiple accounts from one IP detected. Access banned."
                }

        else:
            conn.execute(
                """
                INSERT INTO ip_accounts
                (ip, telegram_id, username, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ip, telegram_id, username, now, now)
            )

        # Update last activity for the same account.
        conn.execute(
            """
            UPDATE ip_accounts
            SET username = ?, last_seen = ?
            WHERE ip = ? AND telegram_id = ?
            """,
            (username, now, ip, telegram_id)
        )

        conn.commit()
        conn.close()

    return True, None


def require_security():
    """
    Helper for protected API routes.
    """
    user = get_verified_user()

    if not user:
        return None, (
            jsonify({
                "success": False,
                "message": "Invalid Telegram Web App authentication."
            }),
            401
        )

    allowed, error = security_check(user)

    if not allowed:
        return None, (jsonify(error), 403)

    return user, None


# ============================================================
# HEALTH
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "service": "online"
    })


# ============================================================
# SECURITY SESSION
# ============================================================

@app.route("/api/security/session", methods=["POST"])
def security_session():
    """
    Call this immediately when the Mini App opens.
    This is the main security gate.
    """
    user, error = require_security()

    if error:
        return error

    return jsonify({
        "success": True,
        "allowed": True,
        "telegramUserId": str(user["id"])
    })


# ============================================================
# TOPUP VERIFICATION
# ============================================================

@app.route("/api/verify-topup", methods=["POST"])
def verify_topup():
    user, error = require_security()

    if error:
        return error

    data = request.get_json(silent=True) or {}
    txid = str(data.get("txid", "")).strip()

    if not txid:
        return jsonify({
            "success": False,
            "message": "TxID is required."
        }), 400

    with db_lock:
        conn = get_db()

        already_used = conn.execute(
            "SELECT txid FROM processed_txids WHERE txid = ?",
            (txid,)
        ).fetchone()

        if already_used:
            conn.close()
            return jsonify({
                "success": False,
                "message": "Invalid or already used TxID."
            }), 400

        # --------------------------------------------------------
        # IMPORTANT:
        # This is still the same amount simulation from your code.
        # Replace this section with your real blockchain verification.
        # --------------------------------------------------------
        simulated_verified_amount = 1.0

        if simulated_verified_amount >= 1.0:
            coins_to_add = int(simulated_verified_amount * 40)

            conn.execute(
                """
                INSERT INTO processed_txids
                (txid, telegram_id, created_at)
                VALUES (?, ?, ?)
                """,
                (txid, str(user["id"]), int(time.time()))
            )

            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "coinsAdded": coins_to_add,
                "amountVerified": simulated_verified_amount
            })

        conn.close()

    return jsonify({
        "success": False,
        "message": "Top up amount below 1 USDT threshold."
    }), 400


# ============================================================
# WITHDRAWAL NOTIFICATION
# ============================================================

@app.route("/api/withdraw-request", methods=["POST"])
def withdraw_request():
    verified_user, error = require_security()

    if error:
        return error

    data = request.get_json(silent=True) or {}

    amount = float(data.get("amount", 0) or 0)
    fee = float(data.get("fee", 0) or 0)
    net = float(data.get("netAmount", 0) or 0)
    address = str(data.get("address", "")).strip()

    user = {
        "id": verified_user.get("id"),
        "username": verified_user.get("username", "N/A")
    }

    msg_text = (
        f"🚨 NEW WITHDRAWAL REQUEST\n\n"
        f"👤 User ID: {user.get('id')}\n"
        f"Username: @{user.get('username', 'N/A')}\n"
        f"💰 Requested: {amount:.4f} USDT\n"
        f"🔻 Fee: {fee:.4f} USDT\n"
        f"✅ Net Payable: {net:.4f} USDT\n"
        f"🏦 Address: {address}"
    )

    try:
        if ADMIN_CHAT_ID:
            telegram_bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=msg_text
            )
    except Exception as e:
        logging.error("Failed to forward withdrawal request: %s", e)

    return jsonify({
        "success": True,
        "status": "queued"
    })


# ============================================================
# ADMIN: BAN / UNBAN
# ============================================================

@app.route("/api/admin/ban-ip", methods=["POST"])
def admin_ban_ip():
    data = request.get_json(silent=True) or {}

    admin_id = str(data.get("admin_id", ""))
    ip = str(data.get("ip", "")).strip()
    reason = str(data.get("reason", "Admin ban")).strip()

    if admin_id != str(ADMIN_CHAT_ID):
        return jsonify({"success": False, "message": "Unauthorized."}), 403

    if not ip:
        return jsonify({"success": False, "message": "IP required."}), 400

    with db_lock:
        conn = get_db()
        conn.execute(
            """
            INSERT OR REPLACE INTO banned_ips
            (ip, telegram_id, reason, created_at)
            VALUES (?, NULL, ?, ?)
            """,
            (ip, reason, int(time.time()))
        )
        conn.commit()
        conn.close()

    return jsonify({"success": True, "message": "IP banned."})


@app.route("/api/admin/unban-ip", methods=["POST"])
def admin_unban_ip():
    data = request.get_json(silent=True) or {}

    admin_id = str(data.get("admin_id", ""))
    ip = str(data.get("ip", "")).strip()

    if admin_id != str(ADMIN_CHAT_ID):
        return jsonify({"success": False, "message": "Unauthorized."}), 403

    with db_lock:
        conn = get_db()
        conn.execute("DELETE FROM banned_ips WHERE ip = ?", (ip,))
        conn.commit()
        conn.close()

    return jsonify({"success": True, "message": "IP unbanned."})


# ============================================================
# TELEGRAM BOT
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="Open Mini App 🚀",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ]
    ])

    await update.message.reply_text(
        text=(
            "Welcome to USDT Mining Platform.\n"
            "Click below to access your dashboard."
        ),
        reply_markup=keyboard
    )


# ============================================================
# RUN
# ============================================================

def run_flask():
    init_db()

    app.run(
        host=HOST,
        port=PORT,
        debug=False,
        threaded=True
    )


def main():
    if BOT_TOKEN == "PUT_NEW_BOT_TOKEN_HERE":
        raise RuntimeError(
            "BOT_TOKEN is not configured. "
            "Create/revoke your token with @BotFather and set the new token."
        )

    init_db()

    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))

    logging.info("Telegram bot starting...")
    logging.info("Security: 1 IP -> 1 Telegram account")
    logging.info("Database: %s", DB_FILE)

    application.run_polling()


if __name__ == "__main__":
    main()
