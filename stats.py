import json
import os
from datetime import datetime

STATS_FILE = "stats.json"

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_user_stat(user_id: int, key: str = None, value=None):
    stats = load_stats()
    uid = str(user_id)

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M")

    if uid not in stats:
        stats[uid] = {
            "first_seen": now_str,
            "last_active": now_str,
            "photos_sent": 0,
            "session_time_sec": 0,
            "clicked_payment": False
        }
    else:
        last_time = datetime.strptime(stats[uid]["last_active"], "%Y-%m-%d %H:%M")
        delta = (now - last_time).total_seconds()
        stats[uid]["session_time_sec"] += int(delta)
        stats[uid]["last_active"] = now_str

    if key == "photo":
        stats[uid]["photos_sent"] += 1
    elif key == "payment":
        stats[uid]["clicked_payment"] = True

    save_stats(stats)

def get_global_stats():
    stats = load_stats()
    now = datetime.now().date()

    total_users = len(stats)
    photo_users = 0
    paid_users = 0
    total_time = 0
    active_today = 0

    for user in stats.values():
        if user["photos_sent"] > 0:
            photo_users += 1
        if user["clicked_payment"]:
            paid_users += 1
        total_time += user.get("session_time_sec", 0)

        try:
            last = datetime.strptime(user["last_active"], "%Y-%m-%d %H:%M").date()
            if last == now:
                active_today += 1
        except:
            pass

    avg_time = int(total_time / total_users) // 60 if total_users else 0

    return {
        "total_users": total_users,
        "photo_users": photo_users,
        "paid_users": paid_users,
        "avg_minutes": avg_time,
        "active_today": active_today
    }

def get_all_user_stats():
    stats = load_stats()
    summary = []

    for uid, user in stats.items():
        minutes = user["session_time_sec"] // 60
        summary.append(
            f"— {uid}: {user['photos_sent']} фото, {minutes} мин, 💳 {'Да' if user['clicked_payment'] else 'Нет'}"
        )

    return "\n".join(summary)
