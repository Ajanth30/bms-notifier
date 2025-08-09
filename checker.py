import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import smtplib
from email.mime.text import MIMEText
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException  # Added imports
import undetected_chromedriver as uc

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

def create_chrome_options():
    """Create fresh ChromeOptions for each attempt"""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless=new")
    return options

def setup_driver():
    """Configure and return a Chrome WebDriver instance"""
    try:
        service = Service(executable_path='/usr/local/bin/chromedriver')
        driver = uc.Chrome(
            options=create_chrome_options(),  # Fresh options each time
            service=service,
            use_subprocess=True
        )
        return driver
    except Exception as e:
        print(f"Primary initialization failed: {str(e)}")
        # Fallback without service specification
        try:
            driver = uc.Chrome(
                options=create_chrome_options(),  # Fresh options each time
                use_subprocess=True
            )
            return driver
        except Exception as fallback_error:
            print(f"Fallback initialization failed: {str(fallback_error)}")
            raise

def check_for_date(date_obj):
    """Check for movie availability on a specific date"""
    date_str = date_obj.strftime("%Y%m%d")
    url = f"{BASE_URL.rstrip('/')}/{date_str}"
    print(f"Checking {url} for {MOVIE_NAME}...")

    for attempt in range(3):
        driver = None
        try:
            driver = setup_driver()
            driver.get(url)
            
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.__movie, div.event, ul#showEvents"))
                )
                # Rest of your checking logic...
                return True
            except TimeoutException:
                print(f"Timeout waiting for elements on attempt {attempt + 1}")
                continue
                
        except WebDriverException as e:
            print(f"WebDriver error on attempt {attempt + 1}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
        finally:
            if driver:
                driver.quit()
        
        if attempt < 2:
            print(f"Retrying... ({attempt + 1}/3)")
            time.sleep(5)
    
    print(f"Failed to check {date_str} after 3 attempts")
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