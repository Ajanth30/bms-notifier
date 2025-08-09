import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import smtplib
from email.mime.text import MIMEText
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# CONFIG via ENV
BASE_URL = os.environ.get("BASE_URL", "https://lk.bookmyshow.com/sri-lanka/cinemas/regal-cinema-jaffna/MCJA/")
MOVIE_NAME = os.environ.get("MOVIE_NAME", "Thalaivan Thalaivii")
EMAIL_FROM = os.environ["EMAIL_FROM"]            # required
EMAIL_TO = os.environ.get("EMAIL_TO", EMAIL_FROM)
EMAIL_PASS = os.environ["EMAIL_PASS"]            # required
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Colombo")

def send_email(date_str, found_times, page_url):
    subject = f"🎬 Booking Alert: {MOVIE_NAME} on {date_str}"
    body = f"Movie: {MOVIE_NAME}\nDate: {date_str}\nShowtimes: {', '.join(found_times)}\n\nOpen the page: {page_url}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    import smtplib
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
    print("Email sent:", subject)

def check_for_date(date_obj):
    date_str = date_obj.strftime("%Y%m%d")
    url = BASE_URL.rstrip("/") + "/" + date_str
    print(f"Checking {url} ...")

    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-software-rasterizer")
    driver = uc.Chrome(options=options)
    
    try:
        driver.get(url)

        # Wait until the showEvents list loads (adjust timeout as needed)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul#showEvents li.list")))

        list_items = driver.find_elements(By.CSS_SELECTOR, "ul#showEvents li.list")

        found_times = []
        for item in list_items:
            try:
                title_el = item.find_element(By.CSS_SELECTOR, "span.__name")
                movie_title = title_el.text.strip()
                if movie_title.lower() == MOVIE_NAME.lower():
                    time_els = item.find_elements(By.CSS_SELECTOR, "div._available a")
                    times = [t.text.strip() for t in time_els]
                    found_times.extend(times)
            except Exception:
                continue

        if found_times:
            print(f"FOUND {MOVIE_NAME} on {date_str} -> {found_times}")
            send_email(date_str, found_times, url)
            return True
        else:
            print(f"Not found: {MOVIE_NAME} on {date_str}")
            return False
    except Exception as e:
        print("Failed to fetch page via Selenium:", e)
        return False
    finally:
        driver.quit()

def main():
    now_local = datetime.now(ZoneInfo(TIMEZONE))
    today = now_local.date()
    tomorrow = today + timedelta(days=1)

    check_for_date(today)
    check_for_date(tomorrow)

if __name__ == "__main__":
    main()
