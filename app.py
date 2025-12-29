import streamlit as st
from src.auth import login_user
import base64
import json
import os

st.set_page_config(page_title="Ứng dụng phân tích môi trường", page_icon="🌤️", layout="centered")

# HÀM THÊM HÌNH NỀN
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        h1 {{
            text-align: center;
            color: white;
            margin-bottom: 2rem;
        }}
        .button-row {{
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-top: 1rem;
        }}
        .button-row button {{
            width: 100%;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

REMEMBER_FILE = "remember.json"

# HÀM KIỂM TRA GHI NHỚ
def load_remembered_user():
    if os.path.exists(REMEMBER_FILE):
        try:
            with open(REMEMBER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def save_remembered_user(username, role):
    with open(REMEMBER_FILE, "w", encoding="utf-8") as f:
        json.dump({"username": username, "role": role}, f)

def clear_remembered_user():
    if os.path.exists(REMEMBER_FILE):
        os.remove(REMEMBER_FILE)

# KHỞI TẠO SESSION
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

# TỰ ĐỘNG ĐĂNG NHẬP NẾU ĐƯỢC GHI NHỚ
remembered = load_remembered_user()
if remembered and not st.session_state.logged_in:
    st.session_state.logged_in = True
    st.session_state.role = remembered["role"]
    st.session_state.username = remembered["username"]
    st.success(f"Chào mừng trở lại, {st.session_state.username} 👋")
    if st.session_state.role == "admin":
        st.switch_page("pages/Trang admin.py")
    else:
        st.switch_page("pages/Trang chủ.py")

# TRANG ĐĂNG NHẬP
def login_page():
    add_bg_from_local("images/pexels-pixabay-76969.jpg")

    st.markdown("<h1>🔐 Đăng nhập</h1>", unsafe_allow_html=True)
    username = st.text_input("Tên đăng nhập")
    password = st.text_input("Mật khẩu", type="password")
    remember = st.checkbox("🔒 Ghi nhớ tôi")

    login_col, register_col = st.columns(2)

    with login_col:
        if st.button("Đăng nhập", use_container_width=True):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.role = user["role"]
                st.session_state.username = user["username"]
                st.success(f"Xin chào {username} 👋")

                if remember:
                    save_remembered_user(username, user["role"])

                if user["role"] == "admin":
                    st.switch_page("pages/Trang admin.py")
                else:
                    st.switch_page("pages/Trang chủ.py")
            else:
                st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")

    with register_col:
        if st.button("Đăng ký tài khoản", use_container_width=True):
            st.switch_page("pages/Đăng ký.py")

# === GIAO DIỆN CHÍNH ===
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        role = st.session_state.role
        username = st.session_state.username

        st.sidebar.title(f"👤 {username}")
        st.sidebar.page_link("pages/Đổi mật khẩu.py", label="🔑 Đổi mật khẩu")
        st.sidebar.page_link("pages/Logout.py", label="🚪 Đăng xuất")

        # nút xóa file ghi nhớ khi đăng xuất
        if st.sidebar.button("🧹 Xóa ghi nhớ đăng nhập"):
            clear_remembered_user()
            st.success("Đã xóa thông tin ghi nhớ!")

if __name__ == "__main__":
    main()
