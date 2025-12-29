import bcrypt
from src.database import get_db

def login_user(username, password):
    db = get_db()
    user = db.users.find_one({"username": username, "active": True})
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return user
    return None

def register_user(username, password):
    db = get_db()
    if db.users.find_one({"username": username}):
        return False
    
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    db.users.insert_one({
        "username": username,
        "password": hashed,
        "role": "user",
        "active": True,
    })
    return True

def change_password(username, old_password, new_password):
    db = get_db()
    user = db.users.find_one({"username": username})
    if user and bcrypt.checkpw(old_password.encode('utf-8'), user['password']):
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        db.users.update_one(
            {"username": username},
            {"$set": {"password": hashed}}
        )
        return True
    return False

def delete_user_account(username: str, password: str) -> tuple[bool, str]:
    """
    Xóa tài khoản user + dữ liệu liên quan
    Trả về (success, message)
    """
    db = get_db()
    users_col = db["users"]
    favorites_col = db["favorites"]

    user = users_col.find_one({"username": username})
    if not user:
        return False, "Không tìm thấy tài khoản."

    if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return False, "Mật khẩu không đúng."

    # ---- XÓA DỮ LIỆU ----
    users_col.delete_one({"username": username})
    favorites_col.delete_one({"username": username})

    return True, "Tài khoản đã được xóa vĩnh viễn."