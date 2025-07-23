import requests
import subprocess
import base64
import json
import os
from pathlib import Path
from telegram import InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import nest_asyncio
import asyncio

# فعال کردن nest_asyncio برای محیط Replit
nest_asyncio.apply()

# مشخصات تلگرام
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

# لینک مخازن گیت‌هاب
GITHUB_LINKS = {
    'vless': 'https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/vless.txt',
    'vmess': 'https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/vmess.txt',
    'ss': 'https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/ss.txt',
    'trojan': 'https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/trojan.txt'
}

# مسیر v2ray-core
V2RAY_PATH = "./v2ray/v2ray"

# تابع تست سرور با v2ray
def test_v2ray(link, proto, timeout=10):
    config_file = "temp_config.json"
    try:
        config = build_v2ray_config(link, proto)
        if not config:
            return False
        with open(config_file, "w") as f:
            json.dump(config, f)
        result = subprocess.run(
            [V2RAY_PATH, "run", "-c", config_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )
        output = result.stdout.decode() + result.stderr.decode()
        if "success" in output.lower() or "connection established" in output.lower():
            return True
    except subprocess.TimeoutExpired:
        print(f"⏱ Timeout برای {proto} link")
    except Exception as e:
        print(f"❌ خطا برای {proto} link: {e}")
    finally:
        if os.path.exists(config_file):
            os.remove(config_file)
    return False

# ساخت config.json برای v2ray
def build_v2ray_config(link, proto):
    try:
        if proto in ["vmess", "vless"]:
            raw = link.split("://")[1]
            decoded = base64.b64decode(raw + "=" * ((4 - len(raw) % 4) % 4)).decode(errors='ignore')
            node = json.loads(decoded)
            return {
                "outbounds": [{
                    "protocol": proto,
                    "settings": {
                        "vnext": [{
                            "address": node["add"],
                            "port": int(node["port"]),
                            "users": [{
                                "id": node["id"],
                                "alterId": node.get("aid", 0),
                                "security": "auto",
                                "encryption": "none" if proto == "vless" else "auto"
                            }]
                        }]
                    }
                }]
            }
        elif proto == "trojan":
            host = link.split("@")[1].split(":")[0]
            port = int(link.split(":")[-1])
            password = link.split("//")[1].split("@")[0]
            return {
                "outbounds": [{
                    "protocol": "trojan",
                    "settings": {
                        "servers": [{
                            "address": host,
                            "port": port,
                            "password": password
                        }]
                    }
                }]
            }
    except Exception as e:
        print(f"⚠️ خطا در ساخت config: {e}")
    return None

# گرفتن سرورهای سالم
def get_healthy_servers(proto):
    res = requests.get(GITHUB_LINKS[proto], timeout=15)
    servers = res.text.strip().splitlines()
    healthy = []
    for link in servers[:10]:  # فقط ۱۰ لینک اول برای سرعت
        if test_v2ray(link, proto):
            healthy.append(link)
    return healthy

# ساخت فایل Subscription
def create_subscription_file(links):
    content = "\\n".join(links)
    file_path = Path("healthy_sub.txt")
    file_path.write_text(content, encoding="utf-8")
    return file_path

# هندلر /start
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != CHAT_ID:
        await update.message.reply_text("❌ شما اجازه دسترسی ندارید.")
        return
    await update.message.reply_text("🚀 در حال تست سرورها...")
    all_healthy_links = []
    msg = ""
    for proto in GITHUB_LINKS:
        healthy = get_healthy_servers(proto)
        if healthy:
            msg += f"✅ {proto.upper()} سالم ({len(healthy)}):\\n"
            msg += "\\n".join(healthy[:3]) + "\\n...\\n\\n"
            all_healthy_links.extend(healthy)
        else:
            msg += f"❌ {proto.upper()} هیچ سرور سالمی ندارد.\\n"
    if not all_healthy_links:
        await update.message.reply_text("❌ هیچ سرور سالمی پیدا نشد.")
        return
    sub_file = create_subscription_file(all_healthy_links)
    await update.message.reply_document(InputFile(sub_file))
    await update.message.reply_text("🎉 لیست سرورهای سالم ارسال شد!")

# اجرای بات
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("🤖 Bot is running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
