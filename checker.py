import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os

def get_showtimes(date):
    url = f"https://lk.bookmyshow.com/sri-lanka/cinemas/regal-cinema-jaffna/MCJA/{date.strftime('%Y%m%d')}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        showtimes_section = soup.find('section', class_='showtimes')
        if not showtimes_section:
            return []
        
        movies = []
        for item in showtimes_section.find_all('li', class_='list'):
            movie_name = item.find('span', class_='__name').text.strip()
            times = [a.text.strip() for a in item.find_all('a', class_='data-enabled time_vrcenter')]
            movies.append({'name': movie_name, 'times': times})
        return movies
    except requests.RequestException as e:
        print(f"Error fetching data for {date}: {e}")
        return []

def send_email(subject, body):
    sender = os.environ.get('EMAIL_FROM')
    password = os.environ.get('EMAIL_PASS')
    receiver = os.environ.get('EMAIL_TO')
    
    if not all([sender, password, receiver]):
        print("Email credentials not set")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    target_movie = os.environ.get('MOVIE_NAME', '').strip()
    if not target_movie:
        print("No target movie specified")
        return

    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    today_showtimes = get_showtimes(today)
    tomorrow_showtimes = get_showtimes(tomorrow)
    
    email_body = ""
    found = False

    for movie in today_showtimes:
        if movie['name'].lower() == target_movie.lower():
            found = True
            email_body += f"{movie['name']} on {today.strftime('%Y-%m-%d')}:\n"
            email_body += f"  Times: {', '.join(movie['times'])}\n\n"
    
    for movie in tomorrow_showtimes:
        if movie['name'].lower() == target_movie.lower():
            found = True
            email_body += f"{movie['name']} on {tomorrow.strftime('%Y-%m-%d')}:\n"
            email_body += f"  Times: {', '.join(movie['times'])}\n\n"
    
    if found:
        send_email(
            f"Showtimes for {target_movie} on {today.strftime('%Y-%m-%d')} and {tomorrow.strftime('%Y-%m-%d')}",
            email_body
        )
    else:
        print(f"Movie '{target_movie}' not found in showtimes")

if __name__ == "__main__":
    main()