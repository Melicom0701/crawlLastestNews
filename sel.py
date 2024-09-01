import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import mysql.connector
import random
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
        image = curr_article.find('img')['src'] if curr_article.find('img') else None
        content = curr_article.find(class_='entry-content').text
        post.image = image
        post.content = content
    except Exception as e:
        print(f"{post.id}: {e}")
def fetch_articles(active_page):
    PostList = []
    try:
        response = requests.get(f"https://thadinn.com/en_US/page/{active_page}")
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')
        if len(articles) == 0:
            return PostList  
        for article in articles:
            try:
                id = article.get('id')
                link = article.find('a')['href']
                title = article.find(class_='read-title').text
                date = article.find(class_='posts-date').text
                author = article.find(class_='posts-author').text
                new_article = Article(id, title, None, author, date, None, link, None)
                PostList.append(new_article)
            except Exception as e:
                print(f"Error processing article: {e}")
    except Exception as e:
        print(f"Error fetching articles from page {active_page}: {e}")
    return PostList

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
        print(f"Error saving article {post.id}: {e}")

def create_pool():
    pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=10, 
        host='localhost',
        port=3306,
        user='root',
        password='12345678',
        database='news'
    )
    return pool

def main():
    max_page = 100 
    pool = create_pool()

    all_posts = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        fetch_futures = [executor.submit(fetch_articles, page) for page in range(1, max_page + 1)]
        for future in as_completed(fetch_futures):
            result = future.result()
            if result:
                all_posts.extend(result)

    print(f"Total number of posts crawled: {len(all_posts)}")
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(fetch_article_data, post) for post in all_posts]
        for future in as_completed(futures):
            future.result()  # To catch exceptions, if any
    with ThreadPoolExecutor(max_workers=10) as executor:
        save_futures = [executor.submit(save_to_mysql, pool, post) for post in all_posts]
        for future in as_completed(save_futures):
            future.result()  # To catch exceptions, if any

    print("Articles saved to MySQL successfully.")

if __name__ == "__main__":
    main()

