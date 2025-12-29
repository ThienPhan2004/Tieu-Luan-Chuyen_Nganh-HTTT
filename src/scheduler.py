from apscheduler.schedulers.blocking import BlockingScheduler
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.openweather_api import fetch_weather_data
import datetime


# === Đường dẫn log ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "scheduler.log")

def log_message(msg: str):
    """Ghi log ra file và in ra màn hình"""
    timestamp = datetime.datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
    message = f"{timestamp} {msg}\n"
    print(message.strip())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message)

# === Danh sách thành phố ===
CN_CITIES = [
    "Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu",
    "Chongqing", "Tianjin", "Wuhan", "Hangzhou", "Nanjing",
    "Xi'an", "Suzhou", "Changsha", "Zhengzhou", "Qingdao",
    "Jinan", "Harbin", "Shenyang", "Dalian", "Fuzhou",
    "Xiamen", "Ningbo", "Wuxi", "Kunming", "Guiyang",
    "Haikou", "Nanchang", "Lanzhou", "Urumqi", "Hohhot",
    "Taiyuan", "Changchun", "Yinchuan", "Lhasa", "Shijiazhuang",
    "Zhuhai", "Zhongshan", "Dongguan", "Foshan", "Huizhou",
    "Nanning", "Xuzhou", "Wenzhou", "Tangshan", "Weifang",
    "Baotou", "Handan", "Hefei", "Luoyang", "Yantai"
]

def crawl_weather_data():
    """Thu thập dữ liệu thời tiết cho 50 thành phố lớn của Trung Quốc"""
    log_message("=== Bắt đầu thu thập dữ liệu thời tiết ===")

    success, failed = 0, 0
    for city in CN_CITIES:
        result = fetch_weather_data(city, save=True)
        if "error" in result:
            failed += 1
            log_message(f"{city}: {result['error']}")
        else:
            success += 1
            log_message(f"{city}: Lưu thành công ({result['timestamp']})")

    log_message(f"--- Kết thúc: {success} thành công, {failed} thất bại ---\n")

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(crawl_weather_data, "cron", hour=10, minute=10)
    scheduler.add_job(crawl_weather_data, "cron", hour=12, minute=15)
    scheduler.add_job(crawl_weather_data, "cron", hour=16, minute=32)
    scheduler.add_job(crawl_weather_data, "cron", hour=22, minute=36)

    log_message("Scheduler khởi động thành công!")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log_message("Scheduler dừng lại.")
        sys.exit(0)
