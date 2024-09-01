from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import random

# Initialize the WebDriver
driver = webdriver.Chrome()

# Article class definition
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
# Scraping the article list
active_page = 1
PostList = []

try:
    while len(PostList) < 10: 
        driver.get(f"https://thadinn.com/en_US/page/{active_page}")
        articles = driver.find_elements(By.TAG_NAME, "article")
        
        if len(articles) == 0:
            break
        
        for article in articles:
            try:
                id = article.get_attribute("id")
                link = article.find_element(By.TAG_NAME, "a").get_attribute("href")
                title = article.find_element(By.CLASS_NAME, "read-title").text
                date = article.find_element(By.CLASS_NAME, "posts-date").text
                author = article.find_element(By.CLASS_NAME, "posts-author").text

                new_article = Article(id, title, None, author, date, None, link, None)
                PostList.append(new_article)
            except Exception as e:
                print(f"Error processing article: {e}")
        
        active_page += 1

    for post in PostList:
        try:
            # Wait random 3-10 seconds
            time.sleep(random.randint(3, 10))
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(post.link)
            
            curr_article = driver.find_element(By.CLASS_NAME, "entry-content-wrap")
            image = curr_article.find_element(By.TAG_NAME, "img").get_attribute("src")  
            content = curr_article.find_element(By.CLASS_NAME, "entry-content").text
            
            post.image = image
            post.content = content
        except Exception as e:
            print(f"Error processing content for post {post.id}: {e}")
        finally:
            driver.switch_to.window(driver.window_handles[0])

except Exception as e:
    print(f"An error occurred during scraping: {e}")
finally:
    input("Press Enter to close the browser...")
    driver.quit()
