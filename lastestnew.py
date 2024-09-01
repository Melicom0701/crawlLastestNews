import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import time
import random
import requests
from bs4 import BeautifulSoup
import mysql.connector

driver = webdriver.Chrome()
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
GMAIL_USERNAME = "sender@gmail.com"
GMAIL_APP_PASSWORD = "app_password"
RECIPIENT_EMAIL = "receiver@gmail.com"
SUBJECT = "Report On Crawling Articles"

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USERNAME
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USERNAME, GMAIL_APP_PASSWORD)
        text = msg.as_string()
        server.sendmail(GMAIL_USERNAME, RECIPIENT_EMAIL, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")

class Article:
    def __init__(self, id=None, title=None, image=None, author=None, date=None, reading_time=None, link=None, content=None):
        self.id = id
        self.title = title
        self.image = image
        self.author = author
        self.date = date
        self.reading_time = reading_time
        self.link = link
        self.content = content

def fetch_article_data(post):
    try:
        time.sleep(random.randint(1, 3))
        response = requests.get(post.link)
        soup = BeautifulSoup(response.text, 'html.parser')
        curr_article = soup.find(class_='entry-content-wrap')
        
        if curr_article:
            image = curr_article.find('img')['src'] if curr_article.find('img') else None
            content = curr_article.find(class_='entry-content').text if curr_article.find(class_='entry-content') else None
            post.image = image
            post.content = content
        else:
            print(f"Could not find the content for article {post.id}")

    except Exception as e:
        print(f"{post.id}: {e}")

def check_article(pool, id):
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM articles WHERE id = %s", (id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Error checking article {id}: {e}")
        return False

def save_to_mysql(pool, post):
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO articles (id, title, image, author, date, link, content)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE
                 title = VALUES(title),
                 image = VALUES(image),
                 author = VALUES(author),
                 date = VALUES(date),
                 link = VALUES(link),
                 content = VALUES(content)"""
        cursor.execute(sql, (post.id, post.title, post.image, post.author, post.date, post.link, post.content))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving article {post.id}: {e} at {current_time}")

def create_pool():
    pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=10, 
        host='localhost',
        port=3306,
        user='root',
        password='12345678',
        database='???'
    )
    return pool

def main():
    pool = create_pool()

    try: 
        driver.get("somewebpage")
        articles = driver.find_elements(By.TAG_NAME, "article")
        if len(articles) == 0:
            raise Exception("No articles found")
        
        is_new = False
        for article in articles:
            id = article.get_attribute("id")
            if check_article(pool, id):
                continue
            link = article.find_element(By.TAG_NAME, "a").get_attribute("href")
            title = article.find_element(By.CLASS_NAME, "read-title").text
            date = article.find_element(By.CLASS_NAME, "posts-date").text
            author = article.find_element(By.CLASS_NAME, "posts-author").text
            new_article = Article(id, title, None, author, date, None, link, None)
            fetch_article_data(new_article)
            save_to_mysql(pool, new_article)
            is_new = True

        if is_new:
            send_email(SUBJECT, f"New articles found at {current_time}")
        else: 
            send_email(SUBJECT, f"No new articles found at {current_time}")

    except Exception as e:
        send_email(SUBJECT, f"Error: {e} at {current_time}")

    finally:
        driver.quit()

if __name__ == "__main__":
    while True:
        main()
        time.sleep(random.randint(600, 900))