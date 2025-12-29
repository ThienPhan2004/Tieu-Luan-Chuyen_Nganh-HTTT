import streamlit as st
from src.database import get_db
import pandas as pd
from datetime import datetime
import os
import base64

# Kiểm tra đăng nhập và quyền
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")

elif st.session_state.role != "admin":
    st.error("❌ Bạn không có quyền truy cập trang này!")
    st.stop()

# HÌNH NỀN
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
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_from_local("images/pexels-brett-sayles-912364.jpg")

# Kết nối DB
db = get_db()
users = db["users"]

st.title("🧩 Trang quản trị hệ thống")
st.subheader("📋 Danh sách tài khoản người dùng")

# --- Lấy dữ liệu user từ DB ---
user_list = list(users.find({}, {"_id": 0, "username": 1, "role": 1}))

if not user_list:
    st.info("Hiện chưa có tài khoản nào trong hệ thống.")
else:
    # Chuyển thành DataFrame để hiển thị
    df = pd.DataFrame(user_list)
    df.rename(columns={
        "username": "Tên đăng nhập",
        "role": "Vai trò"
    }, inplace=True)

    # Hiển thị bảng
    st.dataframe(df, use_container_width=True)

    # Hiển thị tổng số người dùng
    total_users = len(df)
    st.markdown(f"### 👥 Tổng số tài khoản trong hệ thống: **{total_users}**")

st.markdown("---")
st.subheader("🗑️ Xóa tài khoản người dùng")

# Danh sách username (trừ admin đang đăng nhập)
current_admin = st.session_state.username
usernames = [u["username"] for u in user_list if u["username"] != current_admin]

if not usernames:
    st.info("Không có tài khoản nào có thể xóa.")
else:
    selected_user = st.selectbox(
        "Chọn tài khoản cần xóa:",
        usernames,
        key="delete_user_select"
    )

    # checkbox xác nhận
    confirm_delete = st.checkbox(
        f"Tôi xác nhận muốn xóa tài khoản '{selected_user}'",
        key="confirm_delete_user"
    )

    if st.button("❌ XÓA TÀI KHOẢN", key="btn_delete_user"):
        if not confirm_delete:
            st.warning("⚠️ Vui lòng xác nhận trước khi xóa.")
        else:
            result = users.delete_one({"username": selected_user})

            if result.deleted_count == 1:
                st.success(f"✅ Đã xóa tài khoản **{selected_user}**")
                st.experimental_rerun()
            else:
                st.error("❌ Xóa thất bại. Tài khoản có thể không tồn tại.")


st.markdown("---")
st.subheader("📝 Lịch sử Scheduler (scheduler.log)")

# Đường dẫn đúng đến file log
log_path = os.path.join("logs", "scheduler.log")

# Kiểm tra file tồn tại
if not os.path.exists(log_path):
    st.warning("⚠️ Không tìm thấy file logs/scheduler.log.")
else:
    # Đọc toàn bộ log
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    if not lines:
        st.info("📭 File log trống.")
    else:
        # -----------------------------
        #  BIẾN ĐỔI LOG --> DATAFRAME
        # -----------------------------
        log_dates = []
        log_messages = []

        for line in lines:
            line = line.strip()
            # Dạng: [10/11/2025 10:14:06] ...
            try:
                date_str = line.split("]")[0].replace("[", "")
                date_obj = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
            except:
                date_obj = None

            log_dates.append(date_obj)
            log_messages.append(line)

        df_log = pd.DataFrame({
            "Thời gian": log_dates,
            "Nội dung": log_messages
        })

        # -----------------------------
        #  KHUNG TÌM KIẾM THEO NGÀY
        # -----------------------------
        st.markdown("### 🔍 Tìm kiếm theo ngày")

        # Default date = ngày đầu tiên trong log
        min_date = min([d for d in log_dates if d is not None])
        max_date = max([d for d in log_dates if d is not None])

        selected_date = st.date_input(
            "Chọn ngày để lọc log:",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="log_date_filter"
        )

        # Lọc theo ngày user chọn
        filtered_df = df_log[df_log["Thời gian"].dt.date == selected_date]

        if filtered_df.empty:
            st.info("❗ Không có dòng log nào trong ngày này.")
        else:
            # -----------------------------
            #         PHÂN TRANG
            # -----------------------------
            items_per_page = 50
            total_items = len(filtered_df)
            total_pages = (total_items - 1) // items_per_page + 1

            page = st.number_input(
                "Trang:",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1,
                key="log_page"
            )

            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page

            page_df = filtered_df.iloc[start_idx:end_idx]

            # Hiển thị bảng
            st.dataframe(
                page_df,
                use_container_width=True,
                height=400
            )

            st.markdown(f"### 📌 Tổng số dòng log của ngày {selected_date}: **{total_items}**")