import streamlit as st
from src.auth import register_user
import base64
import time

# KIỂM TRA ĐĂNG NHẬP & PHÂN QUYỀN
if st.session_state.logged_in:
    st.error("❌ Phải đăng xuất trước để thực hiện tính năng này!")
    st.stop()

st.set_page_config(page_title="Đăng ký tài khoản", page_icon="📝", layout="centered")

# Hàm thêm hình nền (dùng chung với trang đăng nhập)
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

# Hiển thị giao diện
add_bg_from_local("images/pexels-pixabay-76969.jpg")

st.markdown("<h1>📝 Đăng ký tài khoản mới</h1>", unsafe_allow_html=True)

username = st.text_input("Tên đăng nhập")
password = st.text_input("Mật khẩu", type="password")
confirm_password = st.text_input("Xác nhận mật khẩu", type="password")

# Hai nút căn đều nhau
st.markdown('<div class="button-row">', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    if st.button("Đăng ký", use_container_width=True):
        if password != confirm_password:
            st.error("❌ Mật khẩu xác nhận không khớp!")
        elif register_user(username, password):
            st.success("✅ Đăng ký thành công! Đang quay lại trang đăng nhập...")
            time.sleep(2)
            st.switch_page("app.py")
        else:
            st.warning("⚠️ Tên đăng nhập đã tồn tại!")

with col2:
    if st.button("Quay lại đăng nhập", use_container_width=True):
        st.switch_page("app.py")

st.markdown('</div>', unsafe_allow_html=True)