import streamlit as st
import os
import time
from src.auth import delete_user_account

st.set_page_config(page_title="Xóa tài khoản", page_icon="🗑️")

# KIỂM TRA ĐĂNG NHẬP & QUYỀN
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")

elif st.session_state.role != "user":
    st.error("❌ Chỉ người dùng thông thường mới được truy cập trang này!")
    st.stop()

st.title("🗑️ Xóa tài khoản cá nhân")
st.warning(
    "⚠️ Hành động này **không thể hoàn tác**.\n\n"
    "Toàn bộ tài khoản và dữ liệu liên quan sẽ bị xóa vĩnh viễn."
)

username = st.session_state.username

password = st.text_input(
    "🔑 Nhập mật khẩu để xác nhận xóa",
    type="password"
)

# NÚT XÓA
if st.button("🚨 Xác nhận xóa tài khoản", type="primary"):
    success, message = delete_user_account(username, password)

    if not success:
        st.error(f"❌ {message}")
    else:
        st.success(f"✅ {message}")

        # Xóa remember.json nếu có
        REMEMBER_FILE = "remember.json"
        if os.path.exists(REMEMBER_FILE):
            try:
                os.remove(REMEMBER_FILE)
            except Exception:
                pass

        # Reset session
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None

        time.sleep(2)
        st.switch_page("app.py")