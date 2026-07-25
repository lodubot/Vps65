#!/usr/bin/env python3
"""
🤖 VPS BOT HOSTING MANAGER - Telegram Bot v2.0 (Advanced)
BOT MADE BY @Hx5x5x5x
"""
import os
import sys
import asyncio
import zipfile
import shutil
import subprocess
import json
import time
import re
import traceback
from pathlib import Path
from datetime import datetime, timedelta

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.error import BadRequest

# ==================== ANSI STRIPPER ====================
def strip_ansi(text):
    """Remove ANSI escape sequences from text."""
    if not isinstance(text, str):
        text = str(text)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# ==================== CONFIG DEFAULTS ====================
DEFAULT_CONFIG = {
    "BOT_TOKEN": os.getenv("BOT_TOKEN", ""),
    "ADMIN_IDS": [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()],
    "HOSTED_BOTS_DIR": os.getenv("HOSTED_BOTS_DIR", "/root/hosted_bots"),
    "LOGS_DIR": os.getenv("LOGS_DIR", "/root/hosted_bots_logs"),
    "MAX_BOTS": int(os.getenv("MAX_BOTS", "10")),
    "MAX_ZIP_SIZE_MB": int(os.getenv("MAX_ZIP_SIZE_MB", "50")),
    "AUTO_START_AFTER_DEPLOY": os.getenv("AUTO_START_AFTER_DEPLOY", "true").lower() == "true",
}

# Robust config import - handles syntax errors, missing vars, etc.
_config_loaded = False
if os.path.exists("config.py"):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("config", "config.py")
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        for key in DEFAULT_CONFIG:
            if hasattr(config_module, key):
                globals()[key] = getattr(config_module, key)
                _config_loaded = True
    except Exception:
        _config_loaded = False

if not _config_loaded:
    for key, val in DEFAULT_CONFIG.items():
        globals()[key] = val

os.makedirs(HOSTED_BOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# ==================== CREDITS ====================
CREDIT_OWNER = "@Hx5x5x5x"
CREDIT_TELEGRAM_CHANNEL = "https://t.me/Dev_Null_X_NODE_JS"
CREDIT_YOUTUBE_CHANNEL = "https://www.youtube.com/@Dev_Null_X"
CREDIT_HOME_VIDEO_URL = "https://files.catbox.moe/q6civ6.mp4"
CREDIT_FOOTER = f"\n\n👑 Bot by {CREDIT_OWNER}"

class S:
    BOT = "🤖"
    WHATSAPP = "💬"
    START = "🟢"
    STOP = "🔴"
    RESTART = "🔄"
    LOGS = "📋"
    STATUS = "📊"
    DEPLOY = "📦"
    DELETE = "🗑️"
    CPU = "💻"
    RAM = "🧠"
    DISK = "💾"
    UPTIME = "⏱️"
    ERROR = "❌"
    SUCCESS = "✅"
    WARNING = "⚠️"
    LOADING = "⏳"
    ARROW = "➡️"
    BACK = "🔙"
    HOME = "🏠"
    INFO = "ℹ️"
    SETTINGS = "⚙️"
    REFRESH = "🔄"
    USER = "👤"
    TIME = "🕐"
    FILE = "📁"
    LOCK = "🔒"
    UNLOCK = "🔓"
    CROWN = "👑"
    PACKAGE = "📦"
    DOWNLOAD = "⬇️"
    PHONE = "📱"
    KEY = "🔑"
    SKIP = "⏭️"
    INSTALL = "🔧"
    NODEJS = "🟢"
    PYTHON = "🐍"
    NPM = "📦"
    PIP = "🐍"
    GITHUB = "🐙"
    SINGLE_FILE = "📄"

class PremiumManager:
    PREMIUM_FILE = f"{HOSTED_BOTS_DIR}/.premium_users.json"
    UNLOCK_FILE = f"{HOSTED_BOTS_DIR}/.unlock_state.json"

    @classmethod
    def load_premium(cls):
        if os.path.exists(cls.PREMIUM_FILE):
            try:
                with open(cls.PREMIUM_FILE, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {}

    @classmethod
    def save_premium(cls, data):
        try:
            with open(cls.PREMIUM_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log_error(f"save_premium failed: {e}")

    @classmethod
    def load_unlock(cls):
        if os.path.exists(cls.UNLOCK_FILE):
            try:
                with open(cls.UNLOCK_FILE, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {"unlocked": False}

    @classmethod
    def save_unlock(cls, data):
        try:
            with open(cls.UNLOCK_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log_error(f"save_unlock failed: {e}")

    @classmethod
    def is_unlocked(cls):
        state = cls.load_unlock()
        return state.get("unlocked", False)

    @classmethod
    def set_unlock(cls, unlocked: bool):
        cls.save_unlock({"unlocked": unlocked})

    @classmethod
    def is_premium(cls, user_id: int):
        data = cls.load_premium()
        return str(user_id) in data

    @classmethod
    def add_premium(cls, user_id: int, added_by: int = None):
        data = cls.load_premium()
        data[str(user_id)] = {
            "added_at": datetime.now().isoformat(),
            "added_by": added_by
        }
        cls.save_premium(data)

    @classmethod
    def remove_premium(cls, user_id: int):
        data = cls.load_premium()
        if str(user_id) in data:
            del data[str(user_id)]
            cls.save_premium(data)
            return True
        return False

    @classmethod
    def get_premium_list(cls):
        return cls.load_premium()

    @classmethod
    def can_use_bot(cls, user_id: int):
        if user_id in ADMIN_IDS:
            return True
        if cls.is_unlocked():
            return True
        return cls.is_premium(user_id)

def log_error(msg, extra=None):
    try:
        log_file = f"{LOGS_DIR}/errors.log"
        os.makedirs(LOGS_DIR, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(f"[{datetime.now()}] {msg}\n")
            if extra:
                f.write(f"Extra: {extra}\n")
    except Exception:
        pass

def log_deploy(msg, bot_name="general", extra=None):
    try:
        log_file = f"{LOGS_DIR}/deploy_{bot_name}.log"
        os.makedirs(LOGS_DIR, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(f"[{datetime.now()}] {msg}\n")
            if extra:
                f.write(f"Extra: {extra}\n")
    except Exception:
        pass

def safe_execute(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                pass
            elif "message to edit not found" in str(e):
                pass
            else:
                await send_error(update, f"BadRequest: {str(e)}")
        except Exception as e:
            tb = traceback.format_exc()
            log_error(f"Error in {func.__name__}: {str(e)}\n{tb}", extra={"user_id": getattr(update.effective_user, 'id', 'unknown')})
            await send_error(update, str(e))
    return wrapper

async def send_error(update, msg):
    error_msg = f"{S.ERROR} **Error:** `{str(msg)[:200]}`"
    if update.callback_query:
        try:
            await update.callback_query.answer("Error!", show_alert=True)
        except Exception:
            pass
        try:
            await update.callback_query.edit_message_text(
                error_msg, parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]])
            )
        except Exception:
            pass
    elif update.message:
        await update.message.reply_text(error_msg, parse_mode="Markdown")

# Try to import psutil, but handle if not installed
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    log_error("psutil not installed. VPS status will be limited.")

class SystemMonitor:
    @staticmethod
    def get_stats():
        if not HAS_PSUTIL:
            return {
                'cpu': 0.0, 'ram_used': 0.0, 'ram_total': 0.0,
                'ram_percent': 0.0, 'disk_used': 0.0, 'disk_total': 0.0,
                'disk_percent': 0.0, 'uptime': 0.0
            }
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime = time.time() - psutil.boot_time()
        return {
            'cpu': cpu, 'ram_used': ram.used / (1024**3),
            'ram_total': ram.total / (1024**3), 'ram_percent': ram.percent,
            'disk_used': disk.used / (1024**3), 'disk_total': disk.total / (1024**3),
            'disk_percent': disk.percent, 'uptime': uptime
        }
    @staticmethod
    def format_uptime(seconds):
        td = timedelta(seconds=int(seconds))
        days, hours, minutes = td.days, td.seconds // 3600, (td.seconds % 3600) // 60
        parts = []
        if days: parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        return " ".join(parts) if parts else "0m"

class HostedBot:
    def __init__(self, bot_id, name, bot_dir, bot_type, user_id=None):
        self.bot_id = bot_id
        self.name = name
        self.bot_dir = str(bot_dir)
        self.bot_type = bot_type
        self.user_id = user_id
        self.service_name = f"hosted-bot-{bot_id}"

    def is_running(self):
        try:
            result = subprocess.run(
                ["pm2", "jlist"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout:
                try:
                    processes = json.loads(result.stdout)
                    for proc in processes:
                        if proc.get("name") == self.service_name:
                            status = proc.get("pm2_env", {}).get("status")
                            return status == "online"
                except Exception:
                    pass

            if self.bot_type in ["python", "whatsapp"]:
                result = subprocess.run(
                    ["systemctl", "is-active", self.service_name],
                    capture_output=True, text=True, timeout=5
                )
                return result.stdout.strip() == "active"
            return False
        except Exception as e:
            log_error(f"is_running check failed: {e}")
            return False

    def get_logs(self, lines=30):
        try:
            result = subprocess.run(
                ["pm2", "logs", self.service_name, "--lines", str(lines), "--nostream"],
                capture_output=True, text=True, timeout=15
            )
            if result.stdout and result.stdout.strip():
                return strip_ansi(result.stdout)[-3500:]

            for log_suffix in ["-out.log", "-error.log", ".log"]:
                log_file = f"/root/.pm2/logs/{self.service_name}{log_suffix}"
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        content = f.read()
                        return strip_ansi(content)[-3500:] if content else "No logs yet"

            if self.bot_type in ["python", "whatsapp"]:
                result = subprocess.run(
                    ["journalctl", "-u", self.service_name, "-n", str(lines), "--no-pager"],
                    capture_output=True, text=True, timeout=10
                )
                if result.stdout and result.stdout.strip():
                    return strip_ansi(result.stdout)[-3500:]

            return "No logs available. Bot may not have started yet.\nCheck if credentials are set correctly."
        except Exception as e:
            return f"Error reading logs: {str(e)}"

    def start(self):
        try:
            if self.bot_type == "nodejs":
                pkg_path = os.path.join(self.bot_dir, "package.json")
                use_npm_start = False
                main_file = "index.js"

                if os.path.exists(pkg_path):
                    try:
                        with open(pkg_path) as f:
                            pkg = json.load(f)
                            if pkg.get("scripts", {}).get("start"):
                                use_npm_start = True
                            main_file = pkg.get("main", "index.js")
                    except Exception:
                        pass

                if use_npm_start:
                    result = subprocess.run(
                        ["pm2", "start", "npm", "--name", self.service_name, "--", "start"],
                        capture_output=True, text=True, timeout=30, cwd=self.bot_dir
                    )
                else:
                    target = os.path.join(self.bot_dir, main_file)
                    if not os.path.exists(target):
                        for f in os.listdir(self.bot_dir):
                            if f.endswith('.js'):
                                target = os.path.join(self.bot_dir, f)
                                break
                    result = subprocess.run(
                        ["pm2", "start", target, "--name", self.service_name],
                        capture_output=True, text=True, timeout=30, cwd=self.bot_dir
                    )
                if result.returncode != 0:
                    log_error(f"PM2 start failed for {self.name}: {result.stderr}")
                subprocess.run(["pm2", "save"], capture_output=True, timeout=10)
                return result.returncode == 0

            elif self.bot_type == "whatsapp":
                pkg_path = os.path.join(self.bot_dir, "package.json")
                use_npm_start = False
                main_file = "index.js"

                if os.path.exists(pkg_path):
                    try:
                        with open(pkg_path) as f:
                            pkg = json.load(f)
                            if pkg.get("scripts", {}).get("start"):
                                use_npm_start = True
                    except Exception:
                        pass

                for mf in ["index.js", "main.js", "bot.js", "app.js"]:
                    if os.path.exists(f"{self.bot_dir}/{mf}"):
                        main_file = mf
                        break
                target = os.path.join(self.bot_dir, main_file)

                if use_npm_start:
                    result = subprocess.run(
                        ["pm2", "start", "npm", "--name", self.service_name, "--", "start"],
                        capture_output=True, text=True, timeout=30, cwd=self.bot_dir
                    )
                else:
                    result = subprocess.run(
                        ["pm2", "start", target, "--name", self.service_name, "--cwd", self.bot_dir],
                        capture_output=True, text=True, timeout=30
                    )
                if result.returncode != 0:
                    log_error(f"PM2 start failed for WhatsApp {self.name}: {result.stderr}")
                subprocess.run(["pm2", "save"], capture_output=True, timeout=10)
                return result.returncode == 0

            else:
                eco_path = f"{self.bot_dir}/ecosystem.json"
                if os.path.exists(eco_path):
                    result = subprocess.run(
                        ["pm2", "start", eco_path],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0:
                        subprocess.run(["pm2", "save"], capture_output=True, timeout=10)
                        return True
                    else:
                        log_error(f"PM2 ecosystem start failed: {result.stderr}")

                main_file = "main.py"
                for mf in ["main.py", "bot.py", "app.py", "run.py"]:
                    if os.path.exists(f"{self.bot_dir}/{mf}"):
                        main_file = mf
                        break
                target = os.path.join(self.bot_dir, main_file)

                result = subprocess.run(
                    ["pm2", "start", target, "--name", self.service_name,
                     "--interpreter", "python3", "--cwd", self.bot_dir],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0:
                    log_error(f"PM2 direct start failed for {self.name}: {result.stderr}")

                subprocess.run(["pm2", "save"], capture_output=True, timeout=10)
                subprocess.run(
                    ["systemctl", "start", self.service_name],
                    capture_output=True, text=True, timeout=30
                )
                return True
        except Exception as e:
            log_error(f"Start failed for {self.name}: {e}")
            return False

    def stop(self):
        try:
            subprocess.run(
                ["pm2", "stop", self.service_name],
                capture_output=True, text=True, timeout=30
            )
            if self.bot_type in ["python", "whatsapp"]:
                subprocess.run(
                    ["systemctl", "stop", self.service_name],
                    capture_output=True, text=True, timeout=30
                )
            return True
        except Exception as e:
            log_error(f"Stop failed for {self.name}: {e}")
            return False

    def restart(self):
        try:
            subprocess.run(
                ["pm2", "restart", self.service_name],
                capture_output=True, text=True, timeout=30
            )
            if self.bot_type in ["python", "whatsapp"]:
                subprocess.run(
                    ["systemctl", "restart", self.service_name],
                    capture_output=True, text=True, timeout=30
                )
            return True
        except Exception as e:
            log_error(f"Restart failed for {self.name}: {e}")
            return False

    def install_npm_package(self, package_name):
        try:
            result = subprocess.run(
                ["npm", "install", package_name],
                cwd=self.bot_dir, capture_output=True, text=True, timeout=300
            )
            log_deploy(f"npm install {package_name}: rc={result.returncode}", self.name)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def install_pip_package(self, package_name):
        try:
            result = subprocess.run(
                ["pip3", "install", package_name],
                cwd=self.bot_dir, capture_output=True, text=True, timeout=300
            )
            log_deploy(f"pip install {package_name}: rc={result.returncode}", self.name)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def get_installed_packages(self):
        packages = {}
        if self.bot_type in ["nodejs", "whatsapp"]:
            pkg_json = os.path.join(self.bot_dir, "package.json")
            if os.path.exists(pkg_json):
                try:
                    with open(pkg_json) as f:
                        pkg = json.load(f)
                        packages['dependencies'] = pkg.get('dependencies', {})
                        packages['devDependencies'] = pkg.get('devDependencies', {})
                except Exception:
                    pass
        elif self.bot_type == "python":
            req_file = os.path.join(self.bot_dir, "requirements.txt")
            if os.path.exists(req_file):
                try:
                    with open(req_file) as f:
                        packages['requirements'] = [l.strip() for l in f if l.strip() and not l.startswith('#')]
                except Exception:
                    pass
        return packages

class BotDatabase:
    DB_FILE = f"{HOSTED_BOTS_DIR}/.bot_db.json"

    @classmethod
    def load(cls):
        if os.path.exists(cls.DB_FILE):
            try:
                with open(cls.DB_FILE, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {}

    @classmethod
    def save(cls, data):
        try:
            with open(cls.DB_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            log_error(f"BotDatabase save failed: {e}")

    @classmethod
    def get_all_bots(cls):
        return cls.load()

    @classmethod
    def get_user_bots(cls, user_id):
        data = cls.load()
        if not isinstance(data, dict):
            return {}
        if user_id in ADMIN_IDS:
            return data
        return {k: v for k, v in data.items() if isinstance(v, dict) and v.get('user_id') == user_id}

    @classmethod
    def add_bot(cls, bot_id, name, bot_dir, bot_type, user_id=None, extra_data=None):
        data = cls.load()
        bot_data = {
            'name': name, 'dir': bot_dir, 'type': bot_type,
            'user_id': user_id,
            'created_at': datetime.now().isoformat()
        }
        if extra_data and isinstance(extra_data, dict):
            bot_data.update(extra_data)
        data[bot_id] = bot_data
        cls.save(data)

    @classmethod
    def remove_bot(cls, bot_id):
        data = cls.load()
        if bot_id in data:
            del data[bot_id]
            cls.save(data)

    @classmethod
    def update_bot(cls, bot_id, key, value):
        data = cls.load()
        if bot_id in data and isinstance(data[bot_id], dict):
            data[bot_id][key] = value
            cls.save(data)

class KB:
    @staticmethod
    def main():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.BOT} My Bots", callback_data="my_bots")],
            [InlineKeyboardButton(f"{S.DEPLOY} Deploy New Bot", callback_data="deploy")],
            [InlineKeyboardButton(f"{S.PACKAGE} Package Manager", callback_data="pkg_manager")],
            [InlineKeyboardButton(f"{S.STATUS} VPS Status", callback_data="vps_status")],
            [InlineKeyboardButton(f"{S.SETTINGS} Settings", callback_data="settings")],
            [InlineKeyboardButton(f"{S.CROWN} Owner {CREDIT_OWNER}", url="https://t.me/Hx5x5x5x")],
            [
                InlineKeyboardButton("📢 Telegram Channel", url=CREDIT_TELEGRAM_CHANNEL),
                InlineKeyboardButton("▶️ YouTube", url=CREDIT_YOUTUBE_CHANNEL)
            ]
        ])

    @staticmethod
    def bot_actions(bot_id, is_running, bot_type):
        keyboard = []
        if is_running:
            keyboard.append([
                InlineKeyboardButton(f"{S.STOP} Stop", callback_data=f"stop:{bot_id}"),
                InlineKeyboardButton(f"{S.RESTART} Restart", callback_data=f"restart:{bot_id}")
            ])
        else:
            keyboard.append([InlineKeyboardButton(f"{S.START} Start", callback_data=f"start:{bot_id}")])

        keyboard.append([
            InlineKeyboardButton(f"{S.LOGS} View Logs", callback_data=f"logs:{bot_id}"),
            InlineKeyboardButton(f"{S.STATUS} Bot Status", callback_data=f"bot_status:{bot_id}")
        ])

        keyboard.append([
            InlineKeyboardButton(f"{S.PACKAGE} Packages", callback_data=f"packages:{bot_id}"),
            InlineKeyboardButton(f"{S.INSTALL} Install Pkg", callback_data=f"install_pkg:{bot_id}")
        ])

        keyboard.append([InlineKeyboardButton(f"{S.DELETE} Delete Bot", callback_data=f"delete:{bot_id}")])
        keyboard.append([InlineKeyboardButton(f"{S.BACK} Back", callback_data="my_bots")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back(callback="menu"):
        return InlineKeyboardMarkup([[InlineKeyboardButton(f"{S.BACK} Back", callback_data=callback)]])

    @staticmethod
    def confirm_delete(bot_id):
        return InlineKeyboardMarkup([[
            InlineKeyboardButton(f"No, Cancel", callback_data=f"bot_detail:{bot_id}"),
            InlineKeyboardButton(f"Yes, Delete", callback_data=f"confirm_delete:{bot_id}")
        ]])

    @staticmethod
    def deploy_type():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.NODEJS} Node.js Bot", callback_data="deploy_type:nodejs")],
            [InlineKeyboardButton(f"{S.PYTHON} Python Bot", callback_data="deploy_type:python")],
            [InlineKeyboardButton(f"{S.WHATSAPP} WhatsApp Bot (Baileys)", callback_data="deploy_type:whatsapp")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]
        ])

    @staticmethod
    def premium_menu():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.CROWN} Add Premium User", callback_data="premium_add")],
            [InlineKeyboardButton(f"{S.USER} Remove Premium User", callback_data="premium_remove")],
            [InlineKeyboardButton(f"{S.INFO} List Premium Users", callback_data="premium_list")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="settings")]
        ])

    @staticmethod
    def whatsapp_setup(bot_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.KEY} Set Password", callback_data=f"wa_password:{bot_id}")],
            [InlineKeyboardButton(f"{S.SKIP} Skip Password", callback_data=f"wa_skip_pass:{bot_id}")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="my_bots")]
        ])

    @staticmethod
    def package_manager(bot_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.NPM} Install npm package", callback_data=f"npm_install:{bot_id}")],
            [InlineKeyboardButton(f"{S.PIP} Install pip package", callback_data=f"pip_install:{bot_id}")],
            [InlineKeyboardButton(f"{S.INFO} View Installed", callback_data=f"view_packages:{bot_id}")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
        ])

    @staticmethod
    def install_type_menu():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.NPM} npm install <pkg>", callback_data="install_type:npm")],
            [InlineKeyboardButton(f"{S.PIP} pip install <pkg>", callback_data="install_type:pip")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="pkg_manager")]
        ])

    @staticmethod
    def deploy_advanced():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.NODEJS} Node.js Bot", callback_data="deploy_type:nodejs")],
            [InlineKeyboardButton(f"{S.PYTHON} Python Bot", callback_data="deploy_type:python")],
            [InlineKeyboardButton(f"{S.WHATSAPP} WhatsApp Bot (Baileys)", callback_data="deploy_type:whatsapp")],
            [InlineKeyboardButton(f"{S.GITHUB} Deploy from GitHub", callback_data="deploy_github")],
            [InlineKeyboardButton(f"{S.SINGLE_FILE} Deploy Single File", callback_data="deploy_single_file")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]
        ])

async def check_access(update: Update):
    user = update.effective_user
    if not user:
        return False
    if not PremiumManager.can_use_bot(user.id):
        if update.callback_query:
            try:
                await update.callback_query.answer("Premium Only!", show_alert=True)
            except Exception:
                pass
        elif update.message:
            await update.message.reply_text(
                f"{S.LOCK} **Access Denied**\n\n"
                f"This bot is **locked**.\n"
                f"Only **Premium Users** can access.\n\n"
                f"Your ID: `{user.id}`",
                parse_mode="Markdown"
            )
        return False
    return True

@safe_execute
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    if not PremiumManager.can_use_bot(user.id):
        await update.message.reply_text(
            f"{S.LOCK} **Access Denied**\n\n"
            f"This bot is **locked**.\n"
            f"Only **Premium Users** can access.\n\n"
            f"Your ID: `{user.id}`",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_video(
        video=CREDIT_HOME_VIDEO_URL,
        caption=(
            f"{S.BOT} **VPS Bot Manager v2.0 (Advanced)**\n\n"
            f"{S.NODEJS} Node.js Bots\n"
            f"{S.PYTHON} Python Bots\n"
            f"{S.WHATSAPP} WhatsApp Bots (Baileys)\n"
            f"{S.PACKAGE} Package Manager\n"
            f"{S.GITHUB} GitHub Deploy\n"
            f"{S.SINGLE_FILE} Single File Deploy\n\n"
            f"{S.ARROW} Select an option:"
            f"{CREDIT_FOOTER}"
        ),
        parse_mode="Markdown",
        reply_markup=KB.main()
    )

@safe_execute
async def unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id not in ADMIN_IDS:
        await update.message.reply_text(
            f"{S.ERROR} **Admin Only!**\nYour ID: `{user.id if user else 'unknown'}`", parse_mode="Markdown"
        )
        return

    args = context.args
    if not args or args[0].lower() not in ["on", "off"]:
        current = PremiumManager.is_unlocked()
        status = f"{S.UNLOCK} **UNLOCKED** (Anyone can use)" if current else f"{S.LOCK} **LOCKED** (Premium only)"
        await update.message.reply_text(
            f"{S.SETTINGS} **Unlock Settings**\n\n"
            f"Current: {status}\n\n"
            f"**Usage:**\n"
            f"`/unlock on` - Anyone can use the bot\n"
            f"`/unlock off` - Only Premium Users can use\n\n"
            f"**Admin Commands:**\n"
            f"`/addprem <user_id>` - Add premium user\n"
            f"`/delprem <user_id>` - Remove premium user\n"
            f"`/premusers` - List all premium users",
            parse_mode="Markdown"
        )
        return

    action = args[0].lower()
    if action == "on":
        PremiumManager.set_unlock(True)
        await update.message.reply_text(
            f"{S.UNLOCK} **Bot Unlocked!**\n\n"
            f"Now **anyone** can use this bot.\n"
            f"Use `/unlock off` to restrict to Premium users.",
            parse_mode="Markdown"
        )
    else:
        PremiumManager.set_unlock(False)
        await update.message.reply_text(
            f"{S.LOCK} **Bot Locked!**\n\n"
            f"Now only **Premium Users** can use this bot.\n"
            f"Use `/unlock on` to allow everyone.\n\n"
            f"Manage premium users with `/addprem` and `/delprem`",
            parse_mode="Markdown"
        )

@safe_execute
async def add_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id not in ADMIN_IDS:
        await update.message.reply_text(f"{S.ERROR} **Admin Only!**", parse_mode="Markdown")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            f"{S.ERROR} **Usage:** `/addprem <user_id>`", parse_mode="Markdown"
        )
        return

    try:
        target_id = int(args[0])
        PremiumManager.add_premium(target_id, user.id)
        await update.message.reply_text(
            f"{S.SUCCESS} **Premium Added!**\n\n"
            f"{S.CROWN} User ID: `{target_id}`\n"
            f"{S.USER} Added by: `{user.id}`",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text(f"{S.ERROR} Invalid user ID!", parse_mode="Markdown")

@safe_execute
async def del_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id not in ADMIN_IDS:
        await update.message.reply_text(f"{S.ERROR} **Admin Only!**", parse_mode="Markdown")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            f"{S.ERROR} **Usage:** `/delprem <user_id>`", parse_mode="Markdown"
        )
        return

    try:
        target_id = int(args[0])
        if PremiumManager.remove_premium(target_id):
            await update.message.reply_text(
                f"{S.SUCCESS} **Premium Removed!**\n\n"
                f"{S.USER} User ID: `{target_id}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"{S.WARNING} User `{target_id}` was not premium.", parse_mode="Markdown"
            )
    except ValueError:
        await update.message.reply_text(f"{S.ERROR} Invalid user ID!", parse_mode="Markdown")

@safe_execute
async def list_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id not in ADMIN_IDS:
        await update.message.reply_text(f"{S.ERROR} **Admin Only!**", parse_mode="Markdown")
        return

    premium_users = PremiumManager.get_premium_list()

    if not premium_users:
        await update.message.reply_text(
            f"{S.INFO} **No Premium Users**\n\n"
            f"Use `/addprem <user_id>` to add users.",
            parse_mode="Markdown"
        )
        return

    text = f"{S.CROWN} **Premium Users** ({len(premium_users)})\n{'─' * 25}\n\n"
    for uid, info in premium_users.items():
        added = info.get("added_at", "Unknown")[:10]
        text += f"{S.USER} `{uid}` - Added: `{added}`\n"

    await update.message.reply_text(text, parse_mode="Markdown")

async def safe_edit(query, text, reply_markup=None):
    try:
        is_media_message = bool(
            query.message and (
                query.message.video or query.message.photo or
                query.message.animation or query.message.document
            )
        )
        if is_media_message:
            try:
                await query.message.delete()
            except Exception:
                pass
            await query.message.chat.send_message(text, parse_mode="Markdown", reply_markup=reply_markup)
            return

        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        elif "There is no text in the message to edit" in str(e) or "message to edit" in str(e).lower():
            try:
                await query.message.delete()
            except Exception:
                pass
            await query.message.chat.send_message(text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            raise

@safe_execute
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not await check_access(update):
        return

    try:
        await query.answer()
    except Exception:
        pass

    data = query.data or ""

    # Safely split callback data
    parts = data.split(":")
    action = parts[0] if parts else ""
    bot_id = parts[1] if len(parts) > 1 else ""

    if data == "menu":
        await safe_edit(query,
            f"{S.BOT} **VPS Bot Manager v2.0 (Advanced)**\n\n"
            f"{S.NODEJS} Node.js | {S.PYTHON} Python | {S.WHATSAPP} WhatsApp\n"
            f"{S.PACKAGE} Package Manager\n"
            f"{S.GITHUB} GitHub Deploy\n"
            f"{S.SINGLE_FILE} Single File Deploy\n\n"
            f"{S.ARROW} Select an option:"
            f"{CREDIT_FOOTER}", KB.main())

    elif data == "my_bots":
        await show_bots_list(update, context)

    elif action == "bot_detail" and bot_id:
        await show_bot_detail(update, context, bot_id)

    elif action == "start" and bot_id:
        await handle_action(update, context, bot_id, "start")

    elif action == "stop" and bot_id:
        await handle_action(update, context, bot_id, "stop")

    elif action == "restart" and bot_id:
        await handle_action(update, context, bot_id, "restart")

    elif action == "logs" and bot_id:
        await show_logs(update, context, bot_id)

    elif action == "bot_status" and bot_id:
        await show_bot_status(update, context, bot_id)

    elif action == "delete" and bot_id:
        await confirm_delete(update, context, bot_id)

    elif action == "confirm_delete" and bot_id:
        await delete_bot(update, context, bot_id)

    elif data == "deploy":
        await safe_edit(query, f"{S.DEPLOY} **Deploy New Bot**\n\n{S.ARROW} Select type:", KB.deploy_advanced())

    elif action == "deploy_type" and bot_id:
        bot_type = bot_id
        context.user_data['deploy_type'] = bot_type
        context.user_data['awaiting_zip'] = True

        type_name = {"nodejs": "Node.js", "python": "Python", "whatsapp": "WhatsApp (Baileys)"}.get(bot_type, bot_type.title())

        req_text = ""
        if bot_type == "nodejs":
            req_text = "• `package.json` required"
        elif bot_type == "python":
            req_text = "• `main.py` or `bot.py` required"
        elif bot_type == "whatsapp":
            req_text = "• Baileys-based bot code\n• `package.json` required"

        await safe_edit(query,
            f"{S.DEPLOY} **Deploy {type_name} Bot**\n\n"
            f"{S.ARROW} Send me a **zip file** with your bot code.\n\n"
            f"{S.INFO} Requirements:\n"
            f"{req_text}\n"
            f"• Max: {MAX_ZIP_SIZE_MB}MB",
            KB.back("deploy")
        )

    elif data == "deploy_github":
        context.user_data['awaiting_github_url'] = True
        await safe_edit(query,
            f"{S.GITHUB} **Deploy from GitHub**\n\n"
            f"{S.ARROW} Send me a GitHub repo URL.\n"
            f"Example: `https://github.com/user/repo`",
            KB.back("deploy")
        )

    elif data == "deploy_single_file":
        context.user_data['awaiting_single_file'] = True
        await safe_edit(query,
            f"{S.SINGLE_FILE} **Deploy Single File**\n\n"
            f"{S.ARROW} Send me a `.js` or `.py` file.\n"
            f"Example: `index.js`, `main.py`",
            KB.back("deploy")
        )

    elif data == "vps_status":
        await show_vps_status(update, context)

    elif data == "refresh_vps":
        await show_vps_status(update, context)

    elif data == "settings":
        await show_settings(update, context)

    elif data == "premium_menu":
        await show_premium_menu(update, context)

    elif data == "premium_add":
        context.user_data['awaiting_premium_add'] = True
        await safe_edit(query,
            f"{S.CROWN} **Add Premium User**\n\n"
            f"{S.ARROW} Send me the **User ID** to add as premium.",
            KB.back("premium_menu")
        )

    elif data == "premium_remove":
        context.user_data['awaiting_premium_remove'] = True
        await safe_edit(query,
            f"{S.USER} **Remove Premium User**\n\n"
            f"{S.ARROW} Send me the **User ID** to remove from premium.",
            KB.back("premium_menu")
        )

    elif data == "premium_list":
        await show_premium_list_callback(update, context)

    elif action == "wa_password" and bot_id:
        context.user_data['awaiting_wa_password'] = bot_id
        await safe_edit(query,
            f"{S.KEY} **Set WhatsApp Password**\n\n"
            f"{S.ARROW} Send me the password for this bot.\n"
            f"Users will need this password to use the bot.",
            KB.back(f"bot_detail:{bot_id}")
        )

    elif action == "wa_skip_pass" and bot_id:
        BotDatabase.update_bot(bot_id, 'wa_password', None)
        BotDatabase.update_bot(bot_id, 'wa_password_skipped', True)
        await safe_edit(query,
            f"{S.SKIP} **Password Skipped**\n\n"
            f"No password protection set.\n"
            f"{S.ARROW} Now send the phone number (e.g., 919876543210)",
            KB.back(f"bot_detail:{bot_id}")
        )
        context.user_data['awaiting_wa_phone'] = bot_id

    elif data == "pkg_manager":
        await show_pkg_manager_menu(update, context)

    elif action == "packages" and bot_id:
        await show_installed_packages(update, context, bot_id)

    elif action == "install_pkg" and bot_id:
        context.user_data['install_target_bot'] = bot_id
        await safe_edit(query,
            f"{S.PACKAGE} **Install Package**\n\n"
            f"{S.ARROW} Select package manager:",
            KB.install_type_menu()
        )

    elif action == "npm_install" and bot_id:
        context.user_data['awaiting_npm_pkg'] = bot_id
        await safe_edit(query,
            f"{S.NPM} **Install npm Package**\n\n"
            f"{S.ARROW} Send package name to install.\n"
            f"Examples: `chalk`, `axios`, `@whiskeysockets/baileys`",
            KB.back(f"bot_detail:{bot_id}")
        )

    elif action == "pip_install" and bot_id:
        context.user_data['awaiting_pip_pkg'] = bot_id
        await safe_edit(query,
            f"{S.PIP} **Install pip Package**\n\n"
            f"{S.ARROW} Send package name to install.\n"
            f"Examples: `requests`, `pillow`, `aiohttp`",
            KB.back(f"bot_detail:{bot_id}")
        )

    elif action == "view_packages" and bot_id:
        await show_installed_packages(update, context, bot_id)

    elif action == "install_type":
        pkg_type = bot_id
        context.user_data['install_type'] = pkg_type

        user = update.effective_user
        bots = BotDatabase.get_user_bots(user.id)

        if not bots:
            await safe_edit(query,
                f"{S.WARNING} No bots deployed!",
                KB.back("pkg_manager")
            )
            return

        keyboard = []
        for bid, binfo in bots.items():
            if not isinstance(binfo, dict):
                continue
            btype = binfo.get('type', '')
            bname = binfo.get('name', 'Unknown')
            if pkg_type == "npm" and btype in ['nodejs', 'whatsapp']:
                keyboard.append([InlineKeyboardButton(
                    f"{S.BOT} {bname} ({btype})",
                    callback_data=f"pkg_bot_select:{bid}"
                )])
            elif pkg_type == "pip" and btype == 'python':
                keyboard.append([InlineKeyboardButton(
                    f"{S.BOT} {bname} ({btype})",
                    callback_data=f"pkg_bot_select:{bid}"
                )])

        if not keyboard:
            await safe_edit(query,
                f"{S.WARNING} No compatible bots found for {pkg_type} install!",
                KB.back("pkg_manager")
            )
            return

        keyboard.append([InlineKeyboardButton(f"{S.BACK} Back", callback_data="pkg_manager")])

        await safe_edit(query,
            f"{S.PACKAGE} **Select Bot**\n\n"
            f"Choose a bot to install {pkg_type} package:",
            InlineKeyboardMarkup(keyboard)
        )

    elif action == "pkg_bot_select" and bot_id:
        pkg_type = context.user_data.get('install_type', 'npm')

        if pkg_type == "npm":
            context.user_data['awaiting_npm_pkg'] = bot_id
            await safe_edit(query,
                f"{S.NPM} **Install npm Package**\n\n"
                f"{S.ARROW} Send package name to install.\n"
                f"Examples: `chalk`, `axios`, `express`",
                KB.back(f"bot_detail:{bot_id}")
            )
        else:
            context.user_data['awaiting_pip_pkg'] = bot_id
            await safe_edit(query,
                f"{S.PIP} **Install pip Package**\n\n"
                f"{S.ARROW} Send package name to install.\n"
                f"Examples: `requests`, `pillow`, `aiohttp`",
                KB.back(f"bot_detail:{bot_id}")
            )

async def show_bots_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    if not user:
        return
    bots = BotDatabase.get_user_bots(user.id)

    if not bots:
        await safe_edit(query,
            f"{S.WARNING} **No bots deployed!**\n\n{S.ARROW} Click 'Deploy New Bot'",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.DEPLOY} Deploy New Bot", callback_data="deploy")],
                [InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]
            ])
        )
        return

    keyboard = []
    for bot_id, info in bots.items():
        if not isinstance(info, dict):
            continue
        try:
            bot_obj = HostedBot(bot_id, info.get('name', 'Unknown'), info.get('dir', ''), info.get('type', 'python'), info.get('user_id'))
            status = S.START if bot_obj.is_running() else S.STOP
            type_emoji = {"nodejs": S.NODEJS, "python": S.PYTHON, "whatsapp": S.WHATSAPP}.get(info.get('type', ''), S.BOT)
            keyboard.append([InlineKeyboardButton(f"{status} {type_emoji} {info.get('name', 'Unknown')}", callback_data=f"bot_detail:{bot_id}")])
        except Exception as e:
            log_error(f"show_bots_list error for {bot_id}: {e}")
            continue
    keyboard.append([InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")])

    await safe_edit(query,
        f"{S.BOT} **Your Bots** ({len(bots)}/{MAX_BOTS})\n\n{S.ARROW} Click to manage:",
        InlineKeyboardMarkup(keyboard)
    )

async def show_bot_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    if not user:
        return
    bots = BotDatabase.get_user_bots(user.id)

    if not isinstance(bots, dict) or bot_id not in bots:
        await safe_edit(query, f"{S.ERROR} Bot not found or access denied!", KB.back("my_bots"))
        return

    info = bots[bot_id]
    if not isinstance(info, dict):
        await safe_edit(query, f"{S.ERROR} Bot data corrupted!", KB.back("my_bots"))
        return

    try:
        bot_obj = HostedBot(bot_id, info.get('name', 'Unknown'), info.get('dir', ''), info.get('type', 'python'), info.get('user_id'))
        is_running = bot_obj.is_running()

        status_emoji = S.START if is_running else S.STOP
        status_text = "Running" if is_running else "Stopped"
        type_emoji = {"nodejs": S.NODEJS, "python": S.PYTHON, "whatsapp": S.WHATSAPP}.get(info.get('type', ''), S.BOT)

        wa_info = ""
        if info.get('type') == 'whatsapp':
            wa_phone = info.get('wa_phone', 'Not set')
            wa_pass = info.get('wa_password')
            wa_info = f"\n{S.PHONE} Phone: `{wa_phone}`\n{S.KEY} Password: `{'Set' if wa_pass else 'None'}`\n"

        created = info.get('created_at', '')
        created_str = created[:10] if created else 'Unknown'

        text = (
            f"{type_emoji} **{info.get('name', 'Unknown')}**\n"
            f"{'─' * 25}\n"
            f"{status_emoji} Status: `{status_text}`\n"
            f"{S.FILE} Type: `{info.get('type', 'unknown').title()}`\n"
            f"{S.FILE} Dir: `{info.get('dir', 'N/A')}`\n"
            f"{S.TIME} Created: `{created_str}`"
            f"{wa_info}\n\n"
            f"{S.ARROW} Select action:"
        )

        await safe_edit(query, text, KB.bot_actions(bot_id, is_running, info.get('type', 'python')))
    except Exception as e:
        log_error(f"show_bot_detail error: {e}\n{traceback.format_exc()}")
        await safe_edit(query, f"{S.ERROR} Error loading bot details: {str(e)[:100]}", KB.back("my_bots"))

async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str, action: str):
    query = update.callback_query
    user = update.effective_user
    if not user:
        return
    bots = BotDatabase.get_user_bots(user.id)

    if not isinstance(bots, dict) or bot_id not in bots:
        try:
            await query.answer("Bot not found or access denied!", show_alert=True)
        except Exception:
            pass
        return

    info = bots[bot_id]
    if not isinstance(info, dict):
        try:
            await query.answer("Bot data corrupted!", show_alert=True)
        except Exception:
            pass
        return

    bot_obj = HostedBot(bot_id, info.get('name', 'Unknown'), info.get('dir', ''), info.get('type', 'python'), info.get('user_id'))

    action_texts = {"start": "Starting", "stop": "Stopping", "restart": "Restarting"}

    try:
        await query.edit_message_text(
            f"{S.LOADING} {action_texts.get(action, 'Processing')} **{info.get('name', 'Unknown')}**...",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    success = False
    if action == "start":
        success = bot_obj.start()
    elif action == "stop":
        success = bot_obj.stop()
    elif action == "restart":
        success = bot_obj.restart()

    await asyncio.sleep(1)
    await show_bot_detail(update, context, bot_id)

    try:
        status = f"{S.SUCCESS} {action_texts.get(action, 'Done')}!" if success else f"{S.ERROR} Failed!"
        await query.answer(status, show_alert=True)
    except Exception:
        pass

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    if not user:
        return
    bots = BotDatabase.get_user_bots(user.id)

    if not isinstance(bots, dict) or bot_id not in bots:
        try:
            await query.answer("Bot not found or access denied!", show_alert=True)
        except Exception:
            pass
        return

    info = bots[bot_id]
    if not isinstance(info, dict):
        await safe_edit(query, f"{S.ERROR} Bot data corrupted!", KB.back("my_bots"))
        return

    try:
        await query.edit_message_text(
            f"{S.LOADING} Fetching logs...", parse_mode="Markdown"
        )
    except Exception:
        pass

    try:
        bot_obj = HostedBot(bot_id, info.get('name', 'Unknown'), info.get('dir', ''), info.get('type', 'python'), info.get('user_id'))
        logs = bot_obj.get_logs(30)
        logs = logs.replace("`", "'")

        if len(logs) > 3500:
            logs = logs[-3500:] + "\n\n... (truncated)"

        text = f"{S.LOGS} **Logs: {info.get('name', 'Unknown')}**\n{'─' * 25}\n\n```\n{logs}\n```"

        await safe_edit(query, text, InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.REFRESH} Refresh", callback_data=f"logs:{bot_id}")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
        ]))
    except Exception as e:
        log_error(f"show_logs error: {e}")
        await safe_edit(query, f"{S.ERROR} Error fetching logs: {str(e)[:100]}", KB.back(f"bot_detail:{bot_id}"))

async def show_bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    if not user:
        return
    bots = BotDatabase.get_user_bots(user.id)

    if not isinstance(bots, dict) or bot_id not in bots:
        try:
            await query.answer("Bot not found or access denied!", show_alert=True)
        except Exception:
            pass
        return

    info = bots[bot_id]
    if not isinstance(info, dict):
        await safe_edit(query, f"{S.ERROR} Bot data corrupted!", KB.back("my_bots"))
        return

    try:
        bot_obj = HostedBot(bot_id, info.get('name', 'Unknown'), info.get('dir', ''), info.get('type', 'python'), info.get('user_id'))
        is_running = bot_obj.is_running()

        process_info = "N/A"
        if is_running:
            try:
                result = subprocess.run(
                    ["pm2", "describe", bot_obj.service_name],
                    capture_output=True, text=True, timeout=10
                )
                if result.stdout:
                    process_info = result.stdout[:800]
                else:
                    result = subprocess.run(
                        ["systemctl", "status", bot_obj.service_name],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.stdout:
                        process_info = result.stdout[:800]
            except Exception:
                pass

        process_info = process_info.replace("`", "'")
        status_emoji = S.START if is_running else S.STOP
        type_emoji = {"nodejs": S.NODEJS, "python": S.PYTHON, "whatsapp": S.WHATSAPP}.get(info.get('type', ''), S.BOT)
        created = info.get('created_at', '')
        created_str = created[:19] if created else 'Unknown'

        text = (
            f"{S.STATUS} **Status: {info.get('name', 'Unknown')}**\n"
            f"{'─' * 25}\n"
            f"{type_emoji} Type: `{info.get('type', 'unknown').title()}`\n"
            f"{status_emoji} State: `{'Running' if is_running else 'Stopped'}`\n"
            f"{S.FILE} Path: `{info.get('dir', 'N/A')}`\n"
            f"{S.TIME} Created: `{created_str}`\n\n"
            f"{S.INFO} Process Info:\n"
            f"```\n{process_info}\n```"
        )

        await safe_edit(query, text, InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.REFRESH} Refresh", callback_data=f"bot_status:{bot_id}")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
        ]))
    except Exception as e:
        log_error(f"show_bot_status error: {e}")
        await safe_edit(query, f"{S.ERROR} Error fetching status: {str(e)[:100]}", KB.back(f"bot_detail:{bot_id}"))

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    if not user:
        return
    bots = BotDatabase.get_user_bots(user.id)

    if not isinstance(bots, dict) or bot_id not in bots:
        try:
            await query.answer("Bot not found or access denied!", show_alert=True)
        except Exception:
            pass
        return

    info = bots[bot_id]
    if not isinstance(info, dict):
        await safe_edit(query, f"{S.ERROR} Bot data corrupted!", KB.back("my_bots"))
        return

    await safe_edit(query,
        f"{S.WARNING} **Delete {info.get('name', 'Unknown')}?**\n\n"
        f"This action cannot be undone!",
        KB.confirm_delete(bot_id)
    )

async def delete_bot(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    if not user:
        return
    bots = BotDatabase.get_user_bots(user.id)

    if not isinstance(bots, dict) or bot_id not in bots:
        try:
            await query.answer("Bot not found!", show_alert=True)
        except Exception:
            pass
        return

    info = bots[bot_id]
    if not isinstance(info, dict):
        await safe_edit(query, f"{S.ERROR} Bot data corrupted!", KB.back("my_bots"))
        return

    bot_name = info.get('name', 'Unknown')
    bot_obj = HostedBot(bot_id, bot_name, info.get('dir', ''), info.get('type', 'python'), info.get('user_id'))

    try:
        await query.edit_message_text(
            f"{S.LOADING} Deleting **{bot_name}**...",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    bot_obj.stop()

    try:
        bot_dir = info.get('dir', '')
        if bot_dir and os.path.exists(bot_dir):
            shutil.rmtree(bot_dir, ignore_errors=True)
    except Exception as e:
        log_error(f"Delete dir failed: {e}")

    try:
        subprocess.run(["pm2", "delete", bot_obj.service_name], capture_output=True, timeout=30)
        subprocess.run(["pm2", "save"], capture_output=True, timeout=10)
    except Exception:
        pass

    BotDatabase.remove_bot(bot_id)

    await safe_edit(query,
        f"{S.SUCCESS} **Deleted!**\n\n"
        f"{S.BOT} {bot_name} has been removed.",
        InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.BACK} My Bots", callback_data="my_bots")],
            [InlineKeyboardButton(f"{S.HOME} Main Menu", callback_data="menu")]
        ])
    )

async def show_vps_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        stats = SystemMonitor.get_stats()

        text = (
            f"{S.STATUS} **VPS Status**\n"
            f"{'─' * 25}\n"
            f"{S.CPU} CPU: `{stats['cpu']:.1f}%`\n"
            f"{S.RAM} RAM: `{stats['ram_used']:.1f}/{stats['ram_total']:.1f} GB ({stats['ram_percent']}%)`\n"
            f"{S.DISK} Disk: `{stats['disk_used']:.1f}/{stats['disk_total']:.1f} GB ({stats['disk_percent']}%)`\n"
            f"{S.UPTIME} Uptime: `{SystemMonitor.format_uptime(stats['uptime'])}`\n\n"
            f"{S.ARROW} {len(BotDatabase.get_all_bots())} bots hosted"
        )

        await safe_edit(query, text, InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.REFRESH} Refresh", callback_data="refresh_vps")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]
        ]))
    except Exception as e:
        log_error(f"show_vps_status error: {e}")
        await safe_edit(query, f"{S.ERROR} Error fetching VPS status: {str(e)[:100]}", KB.back("menu"))

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    if not user:
        return

    if user.id in ADMIN_IDS:
        keyboard = [
            [InlineKeyboardButton(f"{S.CROWN} Premium Manager", callback_data="premium_menu")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]
        ]

    await safe_edit(query,
        f"{S.SETTINGS} **Settings**\n\n"
        f"Your ID: `{user.id}`\n"
        f"Admin: {'Yes' if user.id in ADMIN_IDS else 'No'}",
        InlineKeyboardMarkup(keyboard)
    )

async def show_premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_edit(query,
        f"{S.CROWN} **Premium Manager**\n\n"
        f"Manage premium user access.",
        KB.premium_menu()
    )

async def show_premium_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    premium_users = PremiumManager.get_premium_list()

    if not premium_users:
        await safe_edit(query,
            f"{S.INFO} No premium users.",
            KB.back("premium_menu")
        )
        return

    text = f"{S.CROWN} **Premium Users** ({len(premium_users)})\n{'─' * 25}\n\n"
    for uid, info in premium_users.items():
        added = info.get("added_at", "Unknown")[:10]
        text += f"{S.USER} `{uid}` - Added: `{added}`\n"

    await safe_edit(query, text, KB.back("premium_menu"))

async def show_pkg_manager_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    if not user:
        return
    bots = BotDatabase.get_user_bots(user.id)

    if not bots:
        await safe_edit(query,
            f"{S.WARNING} No bots deployed!",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.DEPLOY} Deploy New Bot", callback_data="deploy")],
                [InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]
            ])
        )
        return

    keyboard = []
    for bot_id, info in bots.items():
        if not isinstance(info, dict):
            continue
        type_emoji = {"nodejs": S.NODEJS, "python": S.PYTHON, "whatsapp": S.WHATSAPP}.get(info.get('type', ''), S.BOT)
        keyboard.append([InlineKeyboardButton(
            f"{type_emoji} {info.get('name', 'Unknown')} ({info.get('type', 'unknown')})",
            callback_data=f"install_pkg:{bot_id}"
        )])

    keyboard.append([InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")])

    await safe_edit(query,
        f"{S.PACKAGE} **Package Manager**\n\n"
        f"Select a bot to manage packages:",
        InlineKeyboardMarkup(keyboard)
    )

async def show_installed_packages(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    if not user:
        return
    bots = BotDatabase.get_user_bots(user.id)

    if not isinstance(bots, dict) or bot_id not in bots:
        await safe_edit(query, f"{S.ERROR} Bot not found!", KB.back("pkg_manager"))
        return

    info = bots[bot_id]
    if not isinstance(info, dict):
        await safe_edit(query, f"{S.ERROR} Bot data corrupted!", KB.back("pkg_manager"))
        return

    try:
        bot_obj = HostedBot(bot_id, info.get('name', 'Unknown'), info.get('dir', ''), info.get('type', 'python'), info.get('user_id'))
        packages = bot_obj.get_installed_packages()

        text = f"{S.PACKAGE} **Packages: {info.get('name', 'Unknown')}**\n{'─' * 25}\n\n"

        if not packages:
            text += "No package info available."
        else:
            for key, val in packages.items():
                text += f"*{key}:*\n"
                if isinstance(val, dict):
                    for pkg, ver in list(val.items())[:20]:
                        text += f"  • `{pkg}`: `{ver}`\n"
                    if len(val) > 20:
                        text += f"  ... and {len(val)-20} more\n"
                elif isinstance(val, list):
                    for pkg in val[:20]:
                        text += f"  • `{pkg}`\n"
                    if len(val) > 20:
                        text += f"  ... and {len(val)-20} more\n"

        await safe_edit(query, text, InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
        ]))
    except Exception as e:
        log_error(f"show_installed_packages error: {e}")
        await safe_edit(query, f"{S.ERROR} Error fetching packages: {str(e)[:100]}", KB.back(f"bot_detail:{bot_id}"))

# ==================== MESSAGE HANDLERS ====================

@safe_execute
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    if not PremiumManager.can_use_bot(user.id):
        return

    if context.user_data.get('awaiting_zip') and update.message and update.message.document:
        await handle_zip_deploy(update, context)
        return

    if context.user_data.get('awaiting_github_url') and update.message and update.message.text:
        await handle_github_deploy(update, context)
        return

    if context.user_data.get('awaiting_single_file') and update.message and update.message.document:
        await handle_single_file_deploy(update, context)
        return

    if context.user_data.get('awaiting_premium_add') and update.message and update.message.text:
        try:
            target_id = int(update.message.text.strip())
            PremiumManager.add_premium(target_id, user.id)
            await update.message.reply_text(
                f"{S.SUCCESS} Premium added for `{target_id}`",
                parse_mode="Markdown",
                reply_markup=KB.back("premium_menu")
            )
        except ValueError:
            await update.message.reply_text(f"{S.ERROR} Invalid user ID!")
        context.user_data['awaiting_premium_add'] = False
        return

    if context.user_data.get('awaiting_premium_remove') and update.message and update.message.text:
        try:
            target_id = int(update.message.text.strip())
            if PremiumManager.remove_premium(target_id):
                await update.message.reply_text(
                    f"{S.SUCCESS} Premium removed for `{target_id}`",
                    parse_mode="Markdown",
                    reply_markup=KB.back("premium_menu")
                )
            else:
                await update.message.reply_text(
                    f"{S.WARNING} User was not premium.",
                    reply_markup=KB.back("premium_menu")
                )
        except ValueError:
            await update.message.reply_text(f"{S.ERROR} Invalid user ID!")
        context.user_data['awaiting_premium_remove'] = False
        return

    if context.user_data.get('awaiting_wa_password') and update.message and update.message.text:
        bot_id = context.user_data['awaiting_wa_password']
        password = update.message.text.strip()
        BotDatabase.update_bot(bot_id, 'wa_password', password)
        await update.message.reply_text(
            f"{S.SUCCESS} Password set!\n\n{S.ARROW} Now send the phone number (e.g., 919876543210)",
            reply_markup=KB.back(f"bot_detail:{bot_id}")
        )
        context.user_data['awaiting_wa_password'] = False
        context.user_data['awaiting_wa_phone'] = bot_id
        return

    if context.user_data.get('awaiting_wa_phone') and update.message and update.message.text:
        bot_id = context.user_data['awaiting_wa_phone']
        phone = update.message.text.strip()
        BotDatabase.update_bot(bot_id, 'wa_phone', phone)
        await update.message.reply_text(
            f"{S.SUCCESS} Phone number set!\n\n{S.ARROW} You can now start the bot.",
            reply_markup=KB.back(f"bot_detail:{bot_id}")
        )
        context.user_data['awaiting_wa_phone'] = False
        return

    if context.user_data.get('awaiting_npm_pkg') and update.message and update.message.text:
        bot_id = context.user_data['awaiting_npm_pkg']
        pkg_name = update.message.text.strip()
        bots = BotDatabase.get_user_bots(user.id)

        if isinstance(bots, dict) and bot_id in bots and isinstance(bots[bot_id], dict):
            info = bots[bot_id]
            bot_obj = HostedBot(bot_id, info.get('name', 'Unknown'), info.get('dir', ''), info.get('type', 'python'), info.get('user_id'))
            msg = await update.message.reply_text(f"{S.LOADING} Installing `{pkg_name}`...", parse_mode="Markdown")

            success, stdout, stderr = bot_obj.install_npm_package(pkg_name)

            if success:
                await msg.edit_text(
                    f"{S.SUCCESS} Installed `{pkg_name}`!\n\n```\n{stdout[-500:]}\n```",
                    parse_mode="Markdown",
                    reply_markup=KB.back(f"bot_detail:{bot_id}")
                )
            else:
                await msg.edit_text(
                    f"{S.ERROR} Failed to install `{pkg_name}`\n\n```\n{stderr[-800:]}\n```",
                    parse_mode="Markdown",
                    reply_markup=KB.back(f"bot_detail:{bot_id}")
                )
        context.user_data['awaiting_npm_pkg'] = False
        return

    if context.user_data.get('awaiting_pip_pkg') and update.message and update.message.text:
        bot_id = context.user_data['awaiting_pip_pkg']
        pkg_name = update.message.text.strip()
        bots = BotDatabase.get_user_bots(user.id)

        if isinstance(bots, dict) and bot_id in bots and isinstance(bots[bot_id], dict):
            info = bots[bot_id]
            bot_obj = HostedBot(bot_id, info.get('name', 'Unknown'), info.get('dir', ''), info.get('type', 'python'), info.get('user_id'))
            msg = await update.message.reply_text(f"{S.LOADING} Installing `{pkg_name}`...", parse_mode="Markdown")

            success, stdout, stderr = bot_obj.install_pip_package(pkg_name)

            if success:
                await msg.edit_text(
                    f"{S.SUCCESS} Installed `{pkg_name}`!\n\n```\n{stdout[-500:]}\n```",
                    parse_mode="Markdown",
                    reply_markup=KB.back(f"bot_detail:{bot_id}")
                )
            else:
                await msg.edit_text(
                    f"{S.ERROR} Failed to install `{pkg_name}`\n\n```\n{stderr[-800:]}\n```",
                    parse_mode="Markdown",
                    reply_markup=KB.back(f"bot_detail:{bot_id}")
                )
        context.user_data['awaiting_pip_pkg'] = False
        return

async def handle_zip_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message or not update.message.document:
        return

    document = update.message.document

    if not document.file_name or not document.file_name.endswith('.zip'):
        await update.message.reply_text(f"{S.ERROR} Please send a .zip file!")
        return

    file_size = document.file_size or 0
    if file_size > MAX_ZIP_SIZE_MB * 1024 * 1024:
        await update.message.reply_text(f"{S.ERROR} File too large! Max {MAX_ZIP_SIZE_MB}MB")
        return

    bot_type = context.user_data.get('deploy_type', 'nodejs')
    bot_id = f"{user.id}_{int(time.time())}"
    bot_name = document.file_name.replace('.zip', '')
    bot_dir = os.path.join(HOSTED_BOTS_DIR, bot_id)

    msg = await update.message.reply_text(f"{S.LOADING} Downloading and extracting...")

    try:
        os.makedirs(bot_dir, exist_ok=True)
        file = await context.bot.get_file(document.file_id)
        zip_path = os.path.join(bot_dir, "deploy.zip")
        await file.download_to_drive(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(bot_dir)

        os.remove(zip_path)

        if bot_type in ("nodejs", "whatsapp"):
            pkg_path = os.path.join(bot_dir, "package.json")
            if os.path.exists(pkg_path):
                try:
                    with open(pkg_path) as f:
                        pkg = json.load(f)
                        deps = pkg.get('dependencies', {})
                        if deps:
                            await msg.edit_text(f"{S.LOADING} Installing npm dependencies...")
                            subprocess.run(["npm", "install"], cwd=bot_dir, capture_output=True, timeout=300)
                except Exception:
                    pass

        elif bot_type == "python":
            req_path = os.path.join(bot_dir, "requirements.txt")
            if os.path.exists(req_path):
                await msg.edit_text(f"{S.LOADING} Installing pip dependencies...")
                subprocess.run(["pip3", "install", "-r", req_path], cwd=bot_dir, capture_output=True, timeout=300)

        BotDatabase.add_bot(bot_id, bot_name, bot_dir, bot_type, user.id)
        context.user_data['awaiting_zip'] = False

        if bot_type == "whatsapp":
            await msg.edit_text(
                f"{S.SUCCESS} **WhatsApp Bot Deployed!**\n\n"
                f"{S.ARROW} Set password or skip:",
                reply_markup=KB.whatsapp_setup(bot_id)
            )
        else:
            start_text = ""
            if AUTO_START_AFTER_DEPLOY:
                bot_obj = HostedBot(bot_id, bot_name, bot_dir, bot_type, user.id)
                if bot_obj.start():
                    start_text = f"\n{S.SUCCESS} Auto-started!"
                else:
                    start_text = f"\n{S.WARNING} Auto-start failed."

            await msg.edit_text(
                f"{S.SUCCESS} **Deployed!**\n\n"
                f"{S.BOT} Name: `{bot_name}`\n"
                f"{S.FILE} Type: `{bot_type}`\n"
                f"{S.FILE} ID: `{bot_id}`"
                f"{start_text}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"{S.BACK} My Bots", callback_data="my_bots")]
                ])
            )

    except Exception as e:
        log_error(f"ZIP deploy failed: {e}\n{traceback.format_exc()}")
        if bot_dir and os.path.exists(bot_dir):
            shutil.rmtree(bot_dir, ignore_errors=True)
        await msg.edit_text(f"{S.ERROR} Deploy failed: `{str(e)[:200]}`", parse_mode="Markdown")

async def handle_github_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message or not update.message.text:
        return

    url = update.message.text.strip()

    if not re.match(r'https?://github\.com/[\w.-]+/[\w.-]+', url):
        await update.message.reply_text(f"{S.ERROR} Invalid GitHub URL!")
        return

    bot_id = f"{user.id}_{int(time.time())}"
    bot_name = url.split('/')[-1].replace('.git', '')
    bot_dir = os.path.join(HOSTED_BOTS_DIR, bot_id)

    msg = await update.message.reply_text(f"{S.LOADING} Cloning from GitHub...")

    try:
        os.makedirs(bot_dir, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", url, bot_dir],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            await msg.edit_text(f"{S.ERROR} Git clone failed:\n```\n{result.stderr[:500]}\n```", parse_mode="Markdown")
            return

        bot_type = "nodejs"
        if os.path.exists(os.path.join(bot_dir, "requirements.txt")):
            bot_type = "python"
        elif os.path.exists(os.path.join(bot_dir, "package.json")):
            bot_type = "nodejs"

        if bot_type == "nodejs" and os.path.exists(os.path.join(bot_dir, "package.json")):
            await msg.edit_text(f"{S.LOADING} Installing npm dependencies...")
            subprocess.run(["npm", "install"], cwd=bot_dir, capture_output=True, timeout=300)
        elif bot_type == "python" and os.path.exists(os.path.join(bot_dir, "requirements.txt")):
            await msg.edit_text(f"{S.LOADING} Installing pip dependencies...")
            subprocess.run(["pip3", "install", "-r", "requirements.txt"], cwd=bot_dir, capture_output=True, timeout=300)

        BotDatabase.add_bot(bot_id, bot_name, bot_dir, bot_type, user.id)
        context.user_data['awaiting_github_url'] = False

        start_text = ""
        if AUTO_START_AFTER_DEPLOY:
            bot_obj = HostedBot(bot_id, bot_name, bot_dir, bot_type, user.id)
            if bot_obj.start():
                start_text = f"\n{S.SUCCESS} Auto-started!"

        await msg.edit_text(
            f"{S.SUCCESS} **GitHub Deployed!**\n\n"
            f"{S.BOT} Name: `{bot_name}`\n"
            f"{S.FILE} Type: `{bot_type}`\n"
            f"{S.FILE} ID: `{bot_id}`"
            f"{start_text}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.BACK} My Bots", callback_data="my_bots")]
            ])
        )

    except Exception as e:
        log_error(f"GitHub deploy failed: {e}\n{traceback.format_exc()}")
        if bot_dir and os.path.exists(bot_dir):
            shutil.rmtree(bot_dir, ignore_errors=True)
        await msg.edit_text(f"{S.ERROR} Deploy failed: `{str(e)[:200]}`", parse_mode="Markdown")

async def handle_single_file_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message or not update.message.document:
        return

    document = update.message.document

    if not document.file_name or not (document.file_name.endswith('.js') or document.file_name.endswith('.py')):
        await update.message.reply_text(f"{S.ERROR} Please send a .js or .py file!")
        return

    bot_type = "nodejs" if document.file_name.endswith('.js') else "python"
    bot_id = f"{user.id}_{int(time.time())}"
    bot_name = document.file_name
    bot_dir = os.path.join(HOSTED_BOTS_DIR, bot_id)

    msg = await update.message.reply_text(f"{S.LOADING} Saving file...")

    try:
        os.makedirs(bot_dir, exist_ok=True)
        file = await context.bot.get_file(document.file_id)
        file_path = os.path.join(bot_dir, document.file_name)
        await file.download_to_drive(file_path)

        if bot_type == "nodejs" and not os.path.exists(os.path.join(bot_dir, "package.json")):
            pkg = {"name": bot_name.replace('.js', ''), "version": "1.0.0", "main": bot_name}
            with open(os.path.join(bot_dir, "package.json"), 'w') as f:
                json.dump(pkg, f, indent=2)

        BotDatabase.add_bot(bot_id, bot_name, bot_dir, bot_type, user.id)
        context.user_data['awaiting_single_file'] = False

        start_text = ""
        if AUTO_START_AFTER_DEPLOY:
            bot_obj = HostedBot(bot_id, bot_name, bot_dir, bot_type, user.id)
            if bot_obj.start():
                start_text = f"\n{S.SUCCESS} Auto-started!"

        await msg.edit_text(
            f"{S.SUCCESS} **File Deployed!**\n\n"
            f"{S.BOT} Name: `{bot_name}`\n"
            f"{S.FILE} Type: `{bot_type}`\n"
            f"{S.FILE} ID: `{bot_id}`"
            f"{start_text}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.BACK} My Bots", callback_data="my_bots")]
            ])
        )

    except Exception as e:
        log_error(f"Single file deploy failed: {e}\n{traceback.format_exc()}")
        if bot_dir and os.path.exists(bot_dir):
            shutil.rmtree(bot_dir, ignore_errors=True)
        await msg.edit_text(f"{S.ERROR} Deploy failed: `{str(e)[:200]}`", parse_mode="Markdown")

# ==================== MAIN ====================

def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set!")
        print("Set it via environment variable: export BOT_TOKEN='your_token'")
        print("Or create config.py with: BOT_TOKEN = 'your_token'")
        sys.exit(1)

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("unlock", unlock_cmd))
    application.add_handler(CommandHandler("addprem", add_premium_cmd))
    application.add_handler(CommandHandler("delprem", del_premium_cmd))
    application.add_handler(CommandHandler("premusers", list_premium_cmd))

    application.add_handler(CallbackQueryHandler(callback_handler))

    application.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, message_handler))

    print(f"{S.BOT} VPS Bot Manager started!")
    print(f"Admin IDs: {ADMIN_IDS}")
    print(f"Hosted bots dir: {HOSTED_BOTS_DIR}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
