import os, json, datetime, requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNELS = os.environ["CHANNELS"]  # "@dating_batumi,@dating_tbilisi,@dating_georgia"
START_DATE = os.environ.get("START_DATE", "2025-11-04")  # YYYY-MM-DD, день запуска
TZ_OFFSET_HOURS = int(os.environ.get("TZ_OFFSET_HOURS", "4"))  # Asia/Tbilisi = UTC+4

with open("posts.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Определяем индекс дня с момента START_DATE (чтобы каждый день брать следующий пост)
today_utc = datetime.datetime.utcnow()
today_local = today_utc + datetime.timedelta(hours=TZ_OFFSET_HOURS)
day_index = (today_local.date() - datetime.date.fromisoformat(START_DATE)).days
if day_index < 0:
    day_index = 0

def pick_msg(arr):
    # если постов меньше, чем дней, крутим по кругу
    return arr[day_index % len(arr)]

mapping = {
    "@dating_batumi": "batumi",
    "@dating_tbilisi": "tbilisi",
    "@dating_georgia": "georgia"
}

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()

for chat in CHANNELS.split(","):
    chat = chat.strip()
    key = mapping.get(chat)
    if not key or key not in data:
        continue
    msg = pick_msg(data[key])
    # добавим хештеги и призыв к действию
    footer = "\n\n#dating #Georgia #Batumi #Tbilisi #свидания #знакомства"
    try:
        res = send(chat, msg + footer)
        print("Posted to", chat, "message_id:", res.get("result", {}).get("message_id"))
    except Exception as e:
        print("ERROR posting to", chat, "->", e)
