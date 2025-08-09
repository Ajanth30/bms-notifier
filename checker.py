import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import smtplib
from email.mime.text import MIMEText
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configuration
BASE_URL = os.environ.get("BASE_URL","https://lk.bookmyshow.com/sri-lanka/cinemas/regal-cinema-jaffna/MCJA/")
MOVIE_NAME = os.environ.get("MOVIE_NAME", "").strip().lower()
EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_TO = os.environ.get("EMAIL_TO", EMAIL_FROM)
EMAIL_PASS = os.environ["EMAIL_PASS"]
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Colombo")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
MAX_RETRIES = 3
WAIT_TIMEOUT = 20

def send_email(date_str, found_times, page_url):
    """Send notification email about available showtimes"""
    subject = f"🎬 Booking Alert: {MOVIE_NAME.title()} on {date_str}"
    body = (f"Movie: {MOVIE_NAME.title()}\n"
            f"Date: {date_str}\n"
            f"Showtimes: {', '.join(found_times)}\n\n"
            f"Book now: {page_url}")
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.login(EMAIL_FROM, EMAIL_PASS)
                server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(EMAIL_FROM, EMAIL_PASS)
                server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        print(f"Email sent successfully for {date_str}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

def setup_driver():
    """Configure and return a Chrome WebDriver instance"""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless=new")
    options.add_argument("--remote-debugging-port=9222")
    
    # Critical changes for version compatibility:
    driver = uc.Chrome(
        options=options,
        version_main=None,  # Let undetected-chromedriver auto-detect
        driver_executable_path="/usr/local/bin/chromedriver",
        use_subprocess=True
    )
    return driver

def check_for_date(date_obj):
    """Check for movie availability on a specific date"""
    if not MOVIE_NAME:
        print("Error: No movie name specified")
        return False

    date_str = date_obj.strftime("%Y%m%d")
    url = f"{BASE_URL.rstrip('/')}/{date_str}"
    print(f"\nChecking {url} for {MOVIE_NAME}...")

    for attempt in range(1, MAX_RETRIES + 1):
        driver = None
        try:
            driver = setup_driver()
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # Accept cookies if popup appears
            try:
                cookie_accept = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept') or contains(., 'AGREE')]"))
                )
                cookie_accept.click()
                time.sleep(1)
            except TimeoutException:
                pass

            # Wait for movie listings
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.__movie, div.event, ul#showEvents"))
            )

            # Find all movie elements
            movies = driver.find_elements(By.CSS_SELECTOR, "div.__movie, div.event, ul#showEvents li.list")
            found_times = []

            for movie in movies:
                try:
                    title = movie.find_element(
                        By.CSS_SELECTOR, "span.__name, h3.name, a.name"
                    ).text.strip().lower()
                    
                    if MOVIE_NAME in title:
                        times = movie.find_elements(
                            By.CSS_SELECTOR, "div.__time, div.time, a.showtime-pill"
                        )
                        found_times.extend([t.text.strip() for t in times if t.text.strip()])
                except Exception:
                    continue

            if found_times:
                print(f"✅ Found {len(found_times)} showtimes for {MOVIE_NAME} on {date_str}")
                send_email(date_str, found_times, url)
                return True
            else:
                print(f"❌ No showtimes found for {MOVIE_NAME} on {date_str}")
                return False

        except TimeoutException:
            print(f"Attempt {attempt}: Timeout waiting for page elements")
        except WebDriverException as e:
            print(f"Attempt {attempt}: WebDriver error - {str(e)}")
        except Exception as e:
            print(f"Attempt {attempt}: Unexpected error - {str(e)}")
        finally:
            if driver:
                driver.quit()
        
        if attempt < MAX_RETRIES:
            print(f"Retrying... ({attempt + 1}/{MAX_RETRIES})")
            time.sleep(5)

    print(f"Failed to check {date_str} after {MAX_RETRIES} attempts")
    return False

def main():
    """Main function to check for today and tomorrow"""
    now_local = datetime.now(ZoneInfo(TIMEZONE))
    print(f"\n{'-'*40}")
    print(f"Starting check at {now_local.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Movie: {MOVIE_NAME.title() if MOVIE_NAME else 'NOT SPECIFIED'}")
    print(f"Base URL: {BASE_URL}")
    print(f"{'-'*40}\n")

    today = now_local.date()
    tomorrow = today + timedelta(days=1)

    check_for_date(today)
    check_for_date(tomorrow)

if __name__ == "__main__":
    main()