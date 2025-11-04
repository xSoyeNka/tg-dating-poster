import os, json, datetime, requests, sys, pathlib

# ENV из GitHub Secrets
BOT_TOKEN = os.environ["BOT_TOKEN"]                # НЕ хардкодить!
CHANNELS = os.environ["CHANNELS"]                  # "@datingTBS"
START_DATE = os.environ.get("START_DATE", "2025-11-04")
TZ_OFFSET_HOURS = int(os.environ.get("TZ_OFFSET_HOURS", "4"))  # Asia/Tbilisi = UTC+4

print("[DBG] CWD:", os.getcwd())
print("[DBG] Files:", [p.name for p in pathlib.Path(".").iterdir()])
print("[DBG] CHANNELS present:", bool(CHANNELS))
print("[DBG] START_DATE:", START_DATE)

def tg(method, payload):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    r = requests.post(url, json=payload, timeout=30)
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text}
    print(f"[TG] {method} status={r.status_code} → {body}")
    if not body or not body.get("ok"):
        sys.exit(1)
    return body

# sanity check токена
try:
    me = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=15).json()
    print("[TG] getMe:", me)
except Exception as e:
    print("[ERR] getMe exception:", repr(e))
    sys.exit(1)

# читаем посты
try:
    with open("posts.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        print("[ERR] posts.json not a dict")
        sys.exit(1)
    print("[DBG] posts.json keys:", list(data.keys()))
except Exception as e:
    print("[ERR] cannot read posts.json:", repr(e))
    sys.exit(1)

# определяем индекс дня
today_utc = datetime.datetime.utcnow()
today_local = today_utc + datetime.timedelta(hours=TZ_OFFSET_HOURS)
day_index = (today_local.date() - datetime.date.fromisoformat(START_DATE)).days
if day_index < 0:
    day_index = 0
print(f"[INFO] local_date={today_local.date()} day_index={day_index}")

def pick_msg(arr):
    return arr[day_index % len(arr)]

# единственный канал сейчас — @datingTBS → ключ "tbilisi"
mapping = {
    "@datingTBS": "tbilisi"
}

errors = 0
targets = [c.strip() for c in CHANNELS.split(",") if c.strip()]
print("[DBG] Parsed CHANNELS:", targets)

if not targets:
    print("[ERR] CHANNELS is empty")
    sys.exit(1)

for chat in targets:
    key = mapping.get(chat)
    if not key:
        print(f"[WARN] No mapping for {chat}. Known:", list(mapping.keys()))
        errors += 1
        continue
    if key not in data or not data[key]:
        print(f"[WARN] posts.json has no content for key '{key}'")
        errors += 1
        continue

    text = pick_msg(data[key]) + "\n\n#dating #Georgia #Tbilisi #свидания #знакомства"

    print(f"[INFO] Sending to {chat} using key '{key}'")
    try:
        tg("sendMessage", {
            "chat_id": chat,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        })
    except SystemExit:
        errors += 1
    except Exception as e:
        print("[ERR] Exception while sending:", repr(e))
        errors += 1

if errors:
    print(f"[FAIL] Completed with {errors} error(s).")
    sys.exit(1)

print("[DONE] All messages sent successfully.")
