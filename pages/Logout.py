import streamlit as st
import time
import os

st.set_page_config(page_title="Đăng xuất", page_icon="🚪")
st.title("🚪 Đăng xuất khỏi hệ thống")

REMEMBER_FILE = "remember.json"

def clear_remembered_user():
    """Xóa file ghi nhớ nếu tồn tại"""
    if os.path.exists(REMEMBER_FILE):
        os.remove(REMEMBER_FILE)

# Khởi tạo trạng thái xác nhận
if "confirm_logout" not in st.session_state:
    st.session_state.confirm_logout = False

# Nếu chưa xác nhận
if not st.session_state.confirm_logout:
    st.warning("⚠️ Bạn có chắc chắn muốn đăng xuất khỏi hệ thống không?")
    if st.button("✅ Có, đăng xuất"):
        st.session_state.confirm_logout = True
        st.rerun()

# Nếu đã xác nhận
else:
    # Xóa thông tin đăng nhập và ghi nhớ
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    clear_remembered_user()

    st.success("Bạn đã đăng xuất thành công. Tự động quay về trang đăng nhập...")
    time.sleep(2)
    st.session_state.confirm_logout = False
    st.switch_page("app.py")
