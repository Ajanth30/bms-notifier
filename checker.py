# checker.py
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import smtplib
from email.mime.text import MIMEText

# CONFIG via ENV (set these in GitHub Secrets)
BASE_URL = os.environ.get("BASE_URL", "https://lk.bookmyshow.com/sri-lanka/cinemas/regal-cinema-jaffna/MCJA/")
MOVIE_NAME = os.environ.get("MOVIE_NAME", "Thalaivan Thalaivii")
EMAIL_FROM = os.environ["EMAIL_FROM"]            # required
EMAIL_TO = os.environ.get("EMAIL_TO", EMAIL_FROM)
EMAIL_PASS = os.environ["EMAIL_PASS"]            # required
USER_AGENT = os.environ.get("USER_AGENT", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Colombo")  # use Asia/Colombo for local dates

HEADERS = {"User-Agent": USER_AGENT}

def send_email(date_str, found_times, page_url):
    subject = f"🎬 Booking Alert: {MOVIE_NAME} on {date_str}"
    body = f"Movie: {MOVIE_NAME}\nDate: {date_str}\nShowtimes: {', '.join(found_times)}\n\nOpen the page: {page_url}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
    print("Email sent:", subject)

def check_for_date(date_obj):
    date_str = date_obj.strftime("%Y%m%d")
    url = BASE_URL.rstrip("/") + "/" + date_str
    print(f"Checking {url} ...")

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print("Failed to fetch:", e)
        return False

    soup = BeautifulSoup(r.text, "html.parser")
    list_items = soup.select("ul#showEvents li.list")

    found_times = []
    for item in list_items:
        # movie title (robust selector)
        title_el = item.select_one("span.__name")
        if not title_el:
            continue
        movie_title = title_el.get_text(strip=True)
        if movie_title.lower() == MOVIE_NAME.lower():
            times = [a.get_text(strip=True) for a in item.select("div._available a")]
            found_times.extend(times)

    if found_times:
        print(f"FOUND {MOVIE_NAME} on {date_str} -> {found_times}")
        send_email(date_str, found_times, url)
        return True
    else:
        print(f"Not found: {MOVIE_NAME} on {date_str}")
        return False

def main():
    # Use local timezone (Asia/Colombo) for "today"/"tomorrow"
    now_local = datetime.now(ZoneInfo(TIMEZONE))
    today = now_local.date()
    tomorrow = today + timedelta(days=1)

    check_for_date(today)
    check_for_date(tomorrow)

if __name__ == "__main__":
    main()
