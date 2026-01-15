ADMIN_IDS = {
    292972793  # ← твой Telegram ID
}

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
