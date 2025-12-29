import streamlit as st
import base64
from src.openweather_api import fetch_weather_data
from src.database import get_db
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from src.openweather_api import fetch_forecast_7days
import matplotlib.dates as mdates
import pandas as pd
import io

from src.ml_forecast import prepare_features, train_and_predict

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage

from reportlab.platypus import SimpleDocTemplate, Image as RLImage
from reportlab.lib.pagesizes import A4

# KIỂM TRA QUYỀN
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")
elif st.session_state.role != "user":
    st.error("❌ Chỉ người dùng thông thường mới được truy cập trang này!")
    st.stop()

# --- DANH SÁCH 50 THÀNH PHỐ LỚN CỦA TRUNG QUỐC (song ngữ) ---
CN_CITIES = {
    "Beijing": "Bắc Kinh 北京",
    "Shanghai": "Thượng Hải 上海",
    "Guangzhou": "Quảng Châu 广州",
    "Shenzhen": "Thâm Quyến 深圳",
    "Chengdu": "Thành Đô 成都",
    "Chongqing": "Trùng Khánh 重庆",
    "Tianjin": "Thiên Tân 天津",
    "Wuhan": "Vũ Hán 武汉",
    "Hangzhou": "Hàng Châu 杭州",
    "Nanjing": "Nam Kinh 南京",
    "Xi'an": "Tây An 西安",
    "Suzhou": "Tô Châu 苏州",
    "Changsha": "Trường Sa 长沙",
    "Zhengzhou": "Trịnh Châu 郑州",
    "Qingdao": "Thanh Đảo 青岛",
    "Jinan": "Tế Nam 济南",
    "Harbin": "Hắc Long Giang 哈尔滨",
    "Shenyang": "Thẩm Dương 沈阳",
    "Dalian": "Đại Liên 大连",
    "Fuzhou": "Phúc Châu 福州",
    "Xiamen": "Hạ Môn 厦门",
    "Ningbo": "Ninh Ba 宁波",
    "Wuxi": "Vô Tích 无锡",
    "Kunming": "Côn Minh 昆明",
    "Guiyang": "Quý Dương 贵阳",
    "Haikou": "Hải Khẩu 海口",
    "Nanchang": "Nam Xương 南昌",
    "Lanzhou": "Lan Châu 兰州",
    "Urumqi": "Urumqi 乌鲁木齐",
    "Hohhot": "Hohhot 呼和浩特",
    "Taiyuan": "Thái Nguyên 太原",
    "Changchun": "Trường Xuân 长春",
    "Yinchuan": "Ngân Xuyên 银川",
    "Lhasa": "Lhasa 拉萨",
    "Shijiazhuang": "Thạch Gia Trang 石家庄",
    "Zhuhai": "Chu Hải 珠海",
    "Zhongshan": "Trung Sơn 中山",
    "Dongguan": "Đông Quan 东莞",
    "Foshan": "Phật Sơn 佛山",
    "Huizhou": "Huệ Châu 惠州",
    "Nanning": "Nam Ninh 南宁",
    "Xuzhou": "Từ Châu 徐州",
    "Wenzhou": "Vân Châu 温州",
    "Tangshan": "Đường Sơn 唐山",
    "Weifang": "Duy Phường 潍坊",
    "Baotou": "Bảo Đầu 包头",
    "Handan": "Hàm Đan 邯郸",
    "Hefei": "Hợp Phì 合肥",
    "Luoyang": "Lạc Dương 洛阳",
    "Yantai": "Yên Đài  烟台"
}

# ===== HÀM XUẤT BIỂU ĐỒ =====
def export_chart(fig, filename_base):
    state_key = f"export_open_{filename_base}"

    # init state
    if state_key not in st.session_state:
        st.session_state[state_key] = False

    # nút mở export
    if st.button("📤 Xuất biểu đồ", key=f"btn_export_{filename_base}"):
        st.session_state[state_key] = True

    # nếu chưa mở → không render gì thêm
    if not st.session_state[state_key]:
        return

    st.markdown("#### 📁 Chọn định dạng xuất")

    export_format = st.radio(
        "Định dạng:",
        ["PNG", "PDF (ReportLab)", "Excel (XLSX)"],
        key=f"format_{filename_base}"
    )

    # ===== PNG =====
    if export_format == "PNG":
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)

        st.download_button(
            "⬇️ Tải PNG",
            data=buf,
            file_name=f"{filename_base}.png",
            mime="image/png",
            use_container_width=True
        )

    # ===== PDF =====
    elif export_format == "PDF (ReportLab)":
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format="png", dpi=300, bbox_inches="tight")
        img_buf.seek(0)

        pdf_buf = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buf, pagesize=A4)
        doc.build([RLImage(img_buf, width=450, height=300)])
        pdf_buf.seek(0)

        st.download_button(
            "⬇️ Tải PDF",
            data=pdf_buf,
            file_name=f"{filename_base}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # ===== Excel =====
    else:
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format="png", dpi=300, bbox_inches="tight")
        img_buf.seek(0)

        wb = Workbook()
        ws = wb.active
        ws.title = "Chart"
        ws.add_image(XLImage(img_buf), "A1")

        excel_buf = io.BytesIO()
        wb.save(excel_buf)
        excel_buf.seek(0)

        st.download_button(
            "⬇️ Tải Excel",
            data=excel_buf,
            file_name=f"{filename_base}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ===== HÀM MỞ EXPORT MODAL =====
def open_export(key):
    st.session_state[f"export_open_{key}"] = True


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

# GIAO DIỆN CHÍNH
st.title("🌤️ Thông tin môi trường & dự báo")

db = get_db()
username = st.session_state.username
favorites = db["favorites"]

if "weather_data" not in st.session_state:
    st.session_state.weather_data = None

# Hiển thị song ngữ, nhưng chỉ xử lý tên tiếng Anh
col1, col2 = st.columns([4, 1])
with col1:
    display_names = [f"{en} ({zh})" for en, zh in CN_CITIES.items()]
    selected_display = st.selectbox("🏙️ Chọn thành phố:", display_names)

    # Lấy lại phần tên tiếng Anh (trước dấu "(")
    city = selected_display.split(" (")[0]

with col2:
    st.write("")  # căn đều chiều cao
    if st.button("Tìm kiếm", use_container_width=True):
        data = fetch_weather_data(city, save=False)  # chỉ gửi 'Shanghai'
        forecast = fetch_forecast_7days(city)

        if "error" in data:
            st.error(data["error"])
        else:
            st.session_state.weather_data = data
            st.session_state.forecast_data = forecast

# HÀM PHÂN LOẠI AQI
def get_aqi_level(aqi: int):
    if aqi == 1:
        return ("🟢 Tốt (Good)", "#4CAF50")
    elif aqi == 2:
        return ("🟡 Khá (Fair)", "#FFEB3B")
    elif aqi == 3:
        return ("🟠 Trung bình (Moderate)", "#FF9800")
    elif aqi == 4:
        return ("🔴 Kém (Poor)", "#F44336")
    elif aqi == 5:
        return ("🟣 Rất kém (Very Poor)", "#9C27B0")
    else:
        return ("Không xác định", "#9E9E9E")

# HIỂN THỊ DỮ LIỆU
if "weather_data" in st.session_state and st.session_state.weather_data:
    data = st.session_state.weather_data
    forecast_data = st.session_state.get("forecast_data", []) # lấy từ session_state
    components = data.get("components", {})

    st.subheader(f"🌤️ Thời tiết tại {data['city']}")
    st.caption(f"🕒 Cập nhật lúc: {data['timestamp'].strftime('%H:%M — %d/%m/%Y')}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Nhiệt độ", f"{data['temperature']} °C")
        st.metric("Độ ẩm", f"{data['humidity']} %")
        st.metric("Áp suất", f"{data['pressure']} hPa")
    with col2:
        st.metric("Tốc độ gió", f"{data['wind_speed']} m/s")
        st.write(f"**Mô tả:** {data['weather_desc'].capitalize()}")

    # CHỈ SỐ Ô NHIỄM
    aqi_text, aqi_color = get_aqi_level(data["aqi"])
    st.markdown(f"""
        <div style="
            background-color: {aqi_color};
            border-radius: 20px;
            color: white;
            text-align: center;
            padding: 15px;
            font-weight: bold;
            margin-top: 25px;
            font-size: 18px;
        ">
            Chất lượng không khí: {aqi_text} (AQI = {data['aqi']})
        </div>
    """, unsafe_allow_html=True)

    # --- CHỈ SỐ Ô NHIỄM & CÁC KHÍ ---
    st.subheader("☣️ Các chỉ số thành phần không khí")

    components = data.get("components", {})

    pollutants = {
        "co": "CO",
        "no": "NO",
        "no2": "NO₂",
        "o3": "O₃",
        "so2": "SO₂",
        "pm2_5": "PM₂.₅",
        "pm10": "PM₁₀",
        "nh3": "NH₃"
    }

    # === Hàm xác định mức độ và màu ===
    def classify_pollutant(name, value):
        if not isinstance(value, (int, float)):
            return "N/A", "gray"

        levels = {
            "so2": [(0, 20, "Good", "#4CAF50"), (20, 80, "Fair", "#CDDC39"), (80, 250, "Moderate", "#FFC107"),
                    (250, 350, "Poor", "#FF5722"), (350, float("inf"), "Very Poor", "#9C27B0")],
            "no2": [(0, 40, "Good", "#4CAF50"), (40, 70, "Fair", "#CDDC39"), (70, 150, "Moderate", "#FFC107"),
                    (150, 200, "Poor", "#FF5722"), (200, float("inf"), "Very Poor", "#9C27B0")],
            "pm10": [(0, 20, "Good", "#4CAF50"), (20, 50, "Fair", "#CDDC39"), (50, 100, "Moderate", "#FFC107"),
                    (100, 200, "Poor", "#FF5722"), (200, float("inf"), "Very Poor", "#9C27B0")],
            "pm2_5": [(0, 10, "Good", "#4CAF50"), (10, 25, "Fair", "#CDDC39"), (25, 50, "Moderate", "#FFC107"),
                    (50, 75, "Poor", "#FF5722"), (75, float("inf"), "Very Poor", "#9C27B0")],
            "o3": [(0, 60, "Good", "#4CAF50"), (60, 100, "Fair", "#CDDC39"), (100, 140, "Moderate", "#FFC107"),
                (140, 180, "Poor", "#FF5722"), (180, float("inf"), "Very Poor", "#9C27B0")],
            "co": [(0, 4400, "Good", "#4CAF50"), (4400, 9400, "Fair", "#CDDC39"), (9400, 12400, "Moderate", "#FFC107"),
                (12400, 15400, "Poor", "#FF5722"), (15400, float("inf"), "Very Poor", "#9C27B0")],
            "nh3": [(0, 40, "Good", "#4CAF50"), (40, 80, "Fair", "#CDDC39"), (80, 120, "Moderate", "#FFC107"),
                    (120, 160, "Poor", "#FF5722"), (160, float("inf"), "Very Poor", "#9C27B0")],
            "no": [(0, 20, "Good", "#4CAF50"), (20, 40, "Fair", "#CDDC39"), (40, 70, "Moderate", "#FFC107"),
                (70, 100, "Poor", "#FF5722"), (100, float("inf"), "Very Poor", "#9C27B0")],
        }

        for (low, high, label, color) in levels.get(name, []):
            if low <= value < high:
                return label, color
        return "N/A", "gray"

    # --- HIỂN THỊ 2 CỘT ---
    items = list(pollutants.items())
    half = len(items) // 2 + len(items) % 2
    left_items = items[:half]
    right_items = items[half:]

    col1, col2 = st.columns(2)

    def show_metric(col, items):
        for key, label in items:
            value = components.get(key, "N/A")
            level, color = classify_pollutant(key, value)
            if isinstance(value, (int, float)):
                col.markdown(
                    f"""
                    <div style="background-color:{color}; border-radius:10px; padding:8px; margin-bottom:6px; color:white;">
                        <b>{label}</b>: {value:.2f} μg/m³<br>
                        <small>{level}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                col.metric(label, str(value))

    show_metric(col1, left_items)
    show_metric(col2, right_items)

        
    # Nút thêm yêu thích
    user_favorites = favorites.find_one({"username": username}) or {}
    user_fav_list = user_favorites.get("favorites", [])
    is_favorited = data["city"] in user_fav_list

    if is_favorited:
        if st.button("💔 Bỏ khỏi danh sách của tôi"):
            favorites.update_one(
                {"username": username},
                {"$pull": {"favorites": data["city"]}}
            )
            st.session_state.weather_data = data  # Giữ lại hiển thị hiện tại
            st.success(f"Đã bỏ {data['city']} khỏi danh sách của bạn!")
    else:
        if st.button("💖 Thêm vào mục của tôi"):
            favorites.update_one(
                {"username": username},
                {"$addToSet": {"favorites": data["city"]}},
                upsert=True
            )
            st.session_state.weather_data = data
            st.success(f"Đã thêm {data['city']} vào danh sách của bạn!")

    # BẢN ĐỒ BO GÓC
    m = folium.Map(location=[data["lat"], data["lon"]], zoom_start=8)
    folium.Marker([data["lat"], data["lon"]],
                  popup=f"{data['city']} — {data['temperature']}°C, AQI: {data['aqi']}").add_to(m)
    st.markdown("""
        <style>
        .rounded-map iframe {border-radius: 20px; overflow: hidden;}
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="rounded-map">', unsafe_allow_html=True)
    st_folium(m, width=705, height=400)
    st.markdown('</div>', unsafe_allow_html=True)

    # BIỂU ĐỒ DỰ BÁO 7 NGÀY TỪ API
    if st.session_state.get("forecast_data") and isinstance(st.session_state.forecast_data, list):
        forecast_data = st.session_state.forecast_data
        df = pd.DataFrame(forecast_data).sort_values("timestamp")

        dates = df["timestamp"]
        temps_min = df["temp_min"]
        temps_max = df["temp_max"]
        humidity = df.get("humidity")
        rain = df.get("rain")

        st.subheader("📊 Dự báo thời tiết 7 ngày tới")

        fig, ax1 = plt.subplots(figsize=(9, 4))
        ax1.plot(dates, temps_max, label="Cao nhất", color="tomato", marker="o")
        ax1.plot(dates, temps_min, label="Thấp nhất", color="deepskyblue", marker="o")
        ax1.set_xlabel("Ngày")
        ax1.set_ylabel("Nhiệt độ (°C)")
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis="x", rotation=45)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))

        # Trục phụ (mưa, độ ẩm)
        if rain is not None or humidity is not None:
            ax2 = ax1.twinx()
            if rain is not None and not all(pd.isna(rain)):
                ax2.bar(dates, rain, width=0.6, alpha=0.3, color="dodgerblue", label="Lượng mưa (mm)")
            if humidity is not None and not all(pd.isna(humidity)):
                ax2.plot(dates, humidity, color="limegreen", linestyle=":", label="Độ ẩm (%)")
            ax2.set_ylabel("Mưa / Độ ẩm")

        # Gộp chú thích
        lines, labels = ax1.get_legend_handles_labels()
        if rain is not None or humidity is not None:
            lines2, labels2 = ax2.get_legend_handles_labels()
            lines += lines2
            labels += labels2
        ax1.legend(lines, labels, loc="upper right", fontsize=8)

        plt.tight_layout()
        st.pyplot(fig)

        # XUẤT
        filename = f"forecast_7days_weather_{data['city']}"
        export_chart(fig, filename_base=filename)
    else:
        st.info("Không có dữ liệu dự báo 30 ngày cho thành phố này.")


# === PHẦN BIỂU ĐỒ TỪ DỮ LIỆU MONGODB ===
import matplotlib.dates as mdates
from datetime import datetime, time, timedelta

pollutant_keys = ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"]

pollutant_labels = {
    "co": "CO",
    "no": "NO",
    "no2": "NO₂",
    "o3": "O₃",
    "so2": "SO₂",
    "pm2_5": "PM₂.₅",
    "pm10": "PM₁₀",
    "nh3": "NH₃"
}

# ensure DB connection
db = get_db()
weather_col = db["weather_data"]

st.markdown("---")
st.subheader("📊 Phân tích dữ liệu lịch sử")

# Chọn ngày (mặc định: ngày của record hiện tại hoặc hôm nay)
default_date = data["timestamp"].date() if "data" in locals() and data and "timestamp" in data else datetime.utcnow().date()
selected_date = st.date_input("Chọn ngày để xem (dành cho đồ thị theo khung giờ)", value=default_date)

# nút xem chart cho ngày đã chọn
if st.button("Xem biểu đồ theo khung giờ cho ngày đã chọn"):
    st.session_state["slot_chart_date"] = selected_date

if "slot_chart_date" in st.session_state:
    selected_date = st.session_state["slot_chart_date"]

    city = data["city"] if data and "city" in data else None
    if not city:
        st.error("Không có thành phố để tìm — hãy tìm 1 thành phố trước.")
    else:
        slots = {
            "Sáng (07:00-11:00)": (datetime.combine(selected_date, time(7,0)), datetime.combine(selected_date, time(11,45,59))),
            "Trưa (11:30-13:30)": (datetime.combine(selected_date, time(12,0)), datetime.combine(selected_date, time(15,0,59))),
            "Chiều (14:00-18:00)": (datetime.combine(selected_date, time(15,30)), datetime.combine(selected_date, time(18,0,59))),
            "Tối (19:30-23:30)": (datetime.combine(selected_date, time(19,30)), datetime.combine(selected_date, time(23,45,59))),
        }

        slot_names = []
        slot_avg_temps = []

        for name, (start_dt, end_dt) in slots.items():
            q = {"city": city, "timestamp": {"$gte": start_dt, "$lte": end_dt}}
            docs = list(weather_col.find(q, {"temperature": 1}))
            temps = [d["temperature"] for d in docs if d.get("temperature") is not None]
            slot_avg_temps.append(sum(temps)/len(temps) if temps else float("nan"))
            slot_names.append(name)

        fig, ax = plt.subplots(figsize=(8,4))
        ax.bar(slot_names, slot_avg_temps)
        ax.set_title(
            f"Nhiệt độ trung bình theo khung giờ — {city} ({selected_date.strftime('%d/%m/%Y')})"
        )
        ax.set_ylabel("Nhiệt độ trung bình (°C)")
        ax.grid(axis="y", alpha=0.3)

        st.pyplot(fig)

    # NÚT XUẤT
    export_chart(
        fig,
        filename_base=f"slot_avg_temp_{city}_{selected_date.strftime('%Y%m%d')}"
    )

    summary_df = pd.DataFrame({
        "Khung giờ": slot_names,
        "Nhiệt độ TB (°C)": [round(v,2) if not pd.isna(v) else None for v in slot_avg_temps]
    })
    st.dataframe(summary_df, use_container_width=True)


st.markdown("### 📊 Nồng độ khí theo khung giờ")

# nút xem biểu đồ
if st.button("Xem biểu đồ khí theo khung giờ", key="btn_components_by_slot"):
    st.session_state["gas_slot_date"] = selected_date

if "gas_slot_date" in st.session_state:
    selected_date = st.session_state["gas_slot_date"]
    city = data["city"]

    slots = {
            "Sáng (07:00-11:00)": (datetime.combine(selected_date, time(7,0)), datetime.combine(selected_date, time(11,45,59))),
            "Trưa (11:30-13:30)": (datetime.combine(selected_date, time(12,0)), datetime.combine(selected_date, time(15,0,59))),
            "Chiều (14:00-18:00)": (datetime.combine(selected_date, time(15,30)), datetime.combine(selected_date, time(18,0,59))),
            "Tối (19:30-23:30)": (datetime.combine(selected_date, time(19,30)), datetime.combine(selected_date, time(23,45,59))),
        }

    results = {slot: {k: [] for k in pollutant_keys} for slot in slots}

    for slot, (start_dt, end_dt) in slots.items():
        docs = list(weather_col.find(
            {"city": city, "timestamp": {"$gte": start_dt, "$lte": end_dt}},
            {"components": 1}
        ))

        for d in docs:
            comp = d.get("components", {})
            for k in pollutant_keys:
                if isinstance(comp.get(k), (int, float)):
                    results[slot][k].append(comp[k])

    # bảng trung bình
    avg_df = pd.DataFrame({"Khung giờ": list(slots.keys())})
    for k in pollutant_keys:
        avg_df[pollutant_labels[k]] = [
            sum(values[k]) / len(values[k]) if values[k] else None
            for values in results.values()
        ]

    st.dataframe(avg_df, use_container_width=True)

    # ===== VẼ BIỂU ĐỒ =====
    fig, ax = plt.subplots(figsize=(11,5))

    x = range(len(slots))
    width = 0.08
    offset = -(len(pollutant_keys) / 2) * width

    for i, k in enumerate(pollutant_keys):
        ax.bar(
            [p + offset + i * width for p in x],
            avg_df[pollutant_labels[k]],
            width=width,
            label=pollutant_labels[k]
        )

    ax.set_xticks(x)
    ax.set_xticklabels(slots.keys(), rotation=30)
    ax.set_ylabel("μg/m³")
    ax.set_title(
        f"Nồng độ khí theo khung giờ — {city} ({selected_date.strftime('%d/%m/%Y')})"
    )
    ax.legend(ncol=4)
    ax.grid(axis="y", alpha=0.3)

    st.pyplot(fig)

    # ===== EXPORT (ĐÚNG VỊ TRÍ – ĐÚNG KEY) =====
    export_chart(
        fig,
        filename_base=f"gas_components_slot_{city}_{selected_date.strftime('%Y%m%d')}"
    )

# --- Biểu đồ 7 ngày trước (tính từ selected_date hoặc từ hôm nay nếu không chọn) ---
st.markdown("### 📈 Biểu đồ 7 ngày trước (Nhiệt độ cao / thấp / trung bình)")

end_date = st.date_input(
    "Chọn ngày kết thúc cho chuỗi 7 ngày (mặc định = ngày đã chọn)",
    value=selected_date,
    key="enddate_for_7d"
)

start_date = end_date - timedelta(days=6)

# nút vẽ
if st.button("Vẽ đồ thị 7 ngày"):
    st.session_state["chart_7d_window"] = (start_date, end_date)

if "chart_7d_window" in st.session_state:
    start_date, end_date = st.session_state["chart_7d_window"]

    city = data["city"] if data and "city" in data else None
    if not city:
        st.error("Không có thành phố để tìm — hãy tìm 1 thành phố trước.")
    else:
        start_dt = datetime.combine(start_date, time(0,0,0))
        end_dt = datetime.combine(end_date, time(23,59,59))

        q = {"city": city, "timestamp": {"$gte": start_dt, "$lte": end_dt}}
        docs = list(weather_col.find(
            q,
            {"temperature":1, "humidity":1, "pressure":1, "timestamp":1}
        ))

        if not docs:
            st.info("Không tìm thấy dữ liệu trong khoảng thời gian này.")
        else:
            df = pd.DataFrame(docs)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["date"] = df["timestamp"].dt.date

            agg = df.groupby("date").agg(
                temp_max=("temperature", "max"),
                temp_min=("temperature", "min"),
                temp_mean=("temperature", "mean"),
                hum_mean=("humidity", "mean"),
                pres_mean=("pressure", "mean"),
            ).reset_index()

            all_days = pd.date_range(start=start_date, end=end_date).date
            agg = (
                agg.set_index("date")
                .reindex(all_days)
                .rename_axis("date")
                .reset_index()
            )

            # ===== BIỂU ĐỒ NHIỆT ĐỘ =====
            fig1, ax = plt.subplots(figsize=(10,4))
            ax.bar(agg["date"].astype(str), agg["temp_max"], label="Cao nhất", alpha=0.7)
            ax.bar(agg["date"].astype(str), agg["temp_min"], label="Thấp nhất", alpha=0.7)
            ax.plot(
                agg["date"].astype(str),
                agg["temp_mean"],
                marker="o",
                color="black",
                label="Trung bình"
            )
            ax.set_xlabel("Ngày")
            ax.set_ylabel("Nhiệt độ (°C)")
            ax.set_title(
                f"Nhiệt độ 7 ngày — {city} "
                f"({start_date.strftime('%d/%m')} → {end_date.strftime('%d/%m')})"
            )
            ax.legend()
            ax.grid(axis="y", alpha=0.2)
            plt.xticks(rotation=45)

            st.pyplot(fig1)

            export_chart(
                fig1,
                filename_base=(
                    f"temp_7days_{city}_"
                    f"{start_date.strftime('%Y%m%d')}_"
                    f"{end_date.strftime('%Y%m%d')}"
                )
            )

            # ===== BIỂU ĐỒ ĐỘ ẨM & ÁP SUẤT =====
            fig2, ax1 = plt.subplots(figsize=(10,4))
            ax1.plot(
                agg["date"].astype(str),
                agg["hum_mean"],
                marker="o",
                label="Độ ẩm TB (%)"
            )
            ax1.set_xlabel("Ngày")
            ax1.set_ylabel("Độ ẩm (%)")

            ax2 = ax1.twinx()
            ax2.plot(
                agg["date"].astype(str),
                agg["pres_mean"],
                marker="s",
                color="orange",
                label="Áp suất TB (hPa)"
            )
            ax2.set_ylabel("Áp suất (hPa)")

            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

            ax1.set_title(f"Độ ẩm & Áp suất trung bình 7 ngày — {city}")
            ax1.grid(axis="y", alpha=0.15)
            plt.xticks(rotation=45)

            st.pyplot(fig2)

            export_chart(
                fig2,
                filename_base=(
                    f"humidity_pressure_7days_{city}_"
                    f"{start_date.strftime('%Y%m%d')}_"
                    f"{end_date.strftime('%Y%m%d')}"
                )
            )

            # ===== BẢNG =====
            st.markdown("#### Bảng thống kê 7 ngày")
            show_df = agg.copy().round(2)

            st.dataframe(
                show_df.rename(columns={
                    "date": "Ngày",
                    "temp_max": "Nhiệt độ cao nhất (°C)",
                    "temp_min": "Nhiệt độ thấp nhất (°C)",
                    "temp_mean": "Nhiệt độ trung bình (°C)",
                    "hum_mean": "Độ ẩm trung bình (%)",
                    "pres_mean": "Áp suất trung bình (hPa)",
                }),
                use_container_width=True
            )


st.markdown("### 📈 Nồng độ khí 7 ngày")

# nút vẽ
if st.button("Vẽ biểu đồ khí 7 ngày", key="btn_draw_components_7days"):
    st.session_state["gas_7days_window"] = (start_date, end_date)

if "gas_7days_window" in st.session_state:
    start_date, end_date = st.session_state["gas_7days_window"]

    city = data["city"]

    start_dt = datetime.combine(start_date, time(0,0))
    end_dt   = datetime.combine(end_date, time(23,59,59))

    docs = list(weather_col.find(
        {
            "city": city,
            "timestamp": {"$gte": start_dt, "$lte": end_dt}
        },
        {"timestamp": 1, "components": 1}
    ))

    if not docs:
        st.info("Không có dữ liệu khí.")
    else:
        df = pd.DataFrame(docs)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].dt.date

        for k in pollutant_keys:
            df[k] = df["components"].apply(
                lambda c: c.get(k) if isinstance(c, dict) else None
            )

        agg = df.groupby("date")[pollutant_keys].mean()

        all_days = pd.date_range(start=start_date, end=end_date).date
        agg = agg.reindex(all_days)

        # ===== VẼ BIỂU ĐỒ =====
        fig, ax = plt.subplots(figsize=(12,5))

        for k in pollutant_keys:
            ax.plot(
                agg.index.astype(str),
                agg[k],
                marker="o",
                label=pollutant_labels[k]
            )

        ax.set_xlabel("Ngày")
        ax.set_ylabel("μg/m³")
        ax.set_title(
            f"Nồng độ khí 7 ngày — {city} "
            f"({start_date.strftime('%d/%m')} → {end_date.strftime('%d/%m')})"
        )
        ax.grid(alpha=0.3)
        plt.xticks(rotation=45)
        ax.legend(ncol=4)

        st.pyplot(fig)

        # ===== EXPORT (ĐÚNG VỊ TRÍ – ĐÚNG KEY) =====
        export_chart(
            fig,
            filename_base=(
                f"gas_components_7days_{city}_"
                f"{start_date.strftime('%Y%m%d')}_"
                f"{end_date.strftime('%Y%m%d')}"
            )
        )

        # ===== BẢNG =====
        st.dataframe(
            agg.rename(columns=pollutant_labels).round(2),
            use_container_width=True
        )


# === PHẦN DỰ BÁO TỪ DỮ LIỆU MONGODB ===
pollutant_keys = ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"]
pollutant_labels = {
    "co": "CO", "no": "NO", "no2": "NO₂", "o3": "O₃",
    "so2": "SO₂", "pm2_5": "PM₂.₅", "pm10": "PM₁₀", "nh3": "NH₃"
}

other_keys = ["temperature", "humidity", "pressure", "wind_speed"]
other_labels = {
    "temperature": "Nhiệt độ (°C)",
    "humidity": "Độ ẩm (%)",
    "pressure": "Áp suất (hPa)",
    "wind_speed": "Tốc độ gió (m/s)"
}

slot_hour_map = {
    "Sáng": 9,
    "Trưa": 12,
    "Chiều": 15,
    "Tối": 20
}

db = get_db()
weather_col = db["weather_data"]

if "weather_data" not in st.session_state or not st.session_state.weather_data:
    st.warning("Vui lòng tìm kiếm thành phố trước khi dự báo.")
    st.stop()

data = st.session_state.weather_data
city = data["city"]

start_dt = datetime.utcnow() - timedelta(days=60)
docs = list(weather_col.find(
    {"city": city, "timestamp": {"$gte": start_dt}},
    {
        "timestamp": 1,
        "temperature": 1,
        "humidity": 1,
        "pressure": 1,
        "wind_speed": 1,
        "components": 1
    }
))

df = pd.DataFrame(docs)
df["timestamp"] = pd.to_datetime(df["timestamp"])

for k in pollutant_keys:
    df[k] = df["components"].apply(
        lambda c: c.get(k) if isinstance(c, dict) else None
    )

df = prepare_features(df)

feature_cols = [
    "hour", "day", "month",
    "temperature", "humidity",
    "pressure", "wind_speed"
]

st.subheader("🔮 Dự báo nồng độ khí ngày mai")

slot_option = st.selectbox(
    "Chọn khung giờ:",
    ["Sáng (07:00-11:30)", "Trưa (12:00-13:00)",
     "Chiều (13:30-18:00)", "Tối (19:30-23:30)"]
)

if st.button("📈 Dự báo ngày mai", key="btn_predict_gas_tomorrow"):
    st.session_state["forecast_gas_tomorrow_slot"] = slot_option

if "forecast_gas_tomorrow_slot" in st.session_state:
    slot_option = st.session_state["forecast_gas_tomorrow_slot"]

    st.info(f"Đang dự báo cho {city} — {slot_option}")

    # Lấy giờ đại diện
    hour_predict = next(
        v for k, v in slot_hour_map.items() if k in slot_option
    )

    # ===== DÒNG DỰ BÁO =====
    predict_row = {
        "hour": hour_predict,
        "day": datetime.utcnow().day,
        "month": datetime.utcnow().month,
        "temperature": df["temperature"].mean(),
        "humidity": df["humidity"].mean(),
        "pressure": df["pressure"].mean(),
        "wind_speed": df["wind_speed"].mean()
    }

    # ===== DỰ BÁO TỪ ML =====
    results = {
        k: train_and_predict(df, k, feature_cols, predict_row)
        for k in pollutant_keys
    }

    # ===== BẢNG KẾT QUẢ =====
    result_df = pd.DataFrame({
        "Khí": [pollutant_labels[k] for k in pollutant_keys],
        "Giá trị dự báo (μg/m³)": [
            round(results[k], 2) if results[k] is not None else None
            for k in pollutant_keys
        ]
    })

    st.dataframe(result_df, use_container_width=True)

    # ===== BIỂU ĐỒ =====
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(
        pollutant_labels.values(),
        [results[k] for k in pollutant_keys]
    )
    ax.set_ylabel("μg/m³")
    ax.set_title(f"Dự báo nồng độ khí ngày mai — {city} ({slot_option})")
    plt.xticks(rotation=45)
    ax.grid(axis="y", alpha=0.3)

    st.pyplot(fig)

    # ===== LƯU FIG VÀO SESSION =====
    st.session_state["forecast_gas_tomorrow_fig"] = fig

    if "forecast_gas_tomorrow_fig" in st.session_state:
        export_chart(
            st.session_state["forecast_gas_tomorrow_fig"],
            filename_base=f"du_bao_khi_ngaymai_{city}_{slot_option.replace(' ', '_')}"
        )
    else:
        st.warning("Hãy chạy dự báo trước khi xuất biểu đồ.")


st.subheader("🔮 Dự báo nồng độ khí 7 ngày tới")

if st.button("📈 Dự báo 7 ngày", key="btn_predict_gas_7days"):
    st.session_state["run_forecast_gas_7days"] = True

if st.session_state.get("run_forecast_gas_7days"):
    st.info(f"Đang dự báo nồng độ khí 7 ngày cho {city}")

    future_days = pd.date_range(datetime.utcnow(), periods=7)
    future_data = {k: [] for k in pollutant_keys}

    # ===== DÒNG DỰ BÁO GỐC (KHỚP FEATURE_COLS) =====
    base_predict_row = {
        "hour": 12,  # giờ đại diện
        "temperature": df["temperature"].mean(),
        "humidity": df["humidity"].mean(),
        "pressure": df["pressure"].mean(),
        "wind_speed": df["wind_speed"].mean()
    }

    for d in future_days:
        predict_row = base_predict_row.copy()
        predict_row["day"] = d.day
        predict_row["month"] = d.month

        for k in pollutant_keys:
            val = train_and_predict(
                df=df,
                target_col=k,
                feature_cols=feature_cols,   # PHẢI giống lúc fit
                predict_row=predict_row
            )
            future_data[k].append(val)

    # ===== DATAFRAME =====
    forecast_df = pd.DataFrame({
        "Ngày": future_days.strftime("%d/%m"),
        **{pollutant_labels[k]: future_data[k] for k in pollutant_keys}
    })

    st.dataframe(forecast_df.round(2), use_container_width=True)

    fig, ax = plt.subplots(figsize=(12, 6))

    for k in pollutant_keys:
        ax.plot(
            forecast_df["Ngày"],
            future_data[k],
            marker="o",
            label=pollutant_labels[k]
        )

    ax.set_title(f"Dự báo nồng độ khí 7 ngày — {city}")
    ax.set_ylabel("μg/m³")
    ax.grid(alpha=0.3)
    ax.legend(ncol=4)
    plt.xticks(rotation=45)

    st.pyplot(fig)

    # ===== LƯU BIỂU ĐỒ =====
    st.session_state["forecast_gas_7days_fig"] = fig

    if "forecast_gas_7days_fig" in st.session_state:
        export_chart(
            st.session_state["forecast_gas_7days_fig"],
            filename_base=f"du_bao_khi_7ngay_{city}"
        )
    else:
        st.warning("Hãy chạy dự báo trước khi xuất biểu đồ.")


st.subheader("🔮 Dự báo nhiệt độ / độ ẩm / áp suất / gió 7 ngày")

if st.button("📈 Dự báo 7 ngày (other)", key="btn_predict_other_7days_ml"):
    city = data["city"]
    st.info(f"Đang dự báo 7 ngày tới cho {city}...")

    # === LẤY DỮ LIỆU 60 NGÀY GẦN NHẤT ===
    start_dt = datetime.utcnow() - timedelta(days=60)
    docs = list(weather_col.find(
        {"city": city, "timestamp": {"$gte": start_dt}},
        {
            "timestamp": 1,
            "temperature": 1,
            "humidity": 1,
            "pressure": 1,
            "wind_speed": 1
        }
    ))

    if not docs:
        st.error("Không có dữ liệu để dự báo!")
    else:
        df = pd.DataFrame(docs)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # === FEATURE TIME ===
        df["hour"] = df["timestamp"].dt.hour
        df["day"] = df["timestamp"].dt.day
        df["month"] = df["timestamp"].dt.month

        # === FEATURE COLUMNS (PHẢI CỐ ĐỊNH THỨ TỰ) ===
        feature_cols = [
            "hour",
            "day",
            "month",
            "temperature",
            "humidity",
            "pressure",
            "wind_speed"
        ]

        future_days = pd.date_range(datetime.utcnow(), periods=7)
        future_vals = {k: [] for k in other_keys}

        # === DỰ BÁO 7 NGÀY ===
        for d in future_days:
            predict_row = {
                "hour": 12,           # giờ trung bình trong ngày
                "day": d.day,
                "month": d.month,
                "temperature": df["temperature"].mean(),
                "humidity": df["humidity"].mean(),
                "pressure": df["pressure"].mean(),
                "wind_speed": df["wind_speed"].mean()
            }

            for k in other_keys:
                val = train_and_predict(
                    df=df,
                    target_col=k,
                    feature_cols=feature_cols,
                    predict_row=predict_row
                )
                future_vals[k].append(val)

        # === BẢNG KẾT QUẢ ===
        result_df = pd.DataFrame({
            "Ngày": future_days.strftime("%d/%m"),
            **{other_labels[k]: future_vals[k] for k in other_keys}
        })

        st.dataframe(result_df.round(2), use_container_width=True)

        # === BIỂU ĐỒ ===
        fig, ax = plt.subplots(figsize=(10,5))
        for k in other_keys:
            ax.plot(
                result_df["Ngày"],
                result_df[other_labels[k]],
                marker="o",
                label=other_labels[k]
            )

        ax.set_title(f"Dự báo thông số môi trường 7 ngày — {city}")
        ax.set_ylabel("Giá trị")
        ax.grid(alpha=0.3)
        ax.legend()
        plt.xticks(rotation=45)

        st.pyplot(fig)

        # === EXPORT BIỂU ĐỒ ===
        export_chart(
            fig,
            filename_base=f"du_bao_thong_so_7ngay_{city}"
        )