import time
import json
import re
from fastapi import FastAPI, HTTPException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import undetected_chromedriver as uc
from urllib.parse import urlparse, urlunparse
from collections import defaultdict, Counter

app = FastAPI()

# Function to extract links from HTML response
def extract_links(html):
    pattern = r'<a href="(https?://[^\"]+?)\?utm_source=chatgpt.com".*?>(.*?)</a>'
    matches = re.findall(pattern, html)
    links = []
    for url, brandname in matches:
        parsed_url = urlparse(url)
        cleaned_url = urlunparse(parsed_url._replace(query=''))
        host = parsed_url.netloc
        links.append({
            'answer_url': cleaned_url,
            'answer_brandname': re.sub(r'<[^>]+>', '', brandname.strip()),
            'answer_host': host
        })
    return links

# Function to get sentiment from OpenAI
def get_sentiment(answer):
    try:
        # Set up API and model name
        MODEL = "gpt-4o"
        # Simulating a chat with the OpenAI API
        sentiment = "Neutral"  # Mock sentiment, you need to integrate OpenAI here
        return sentiment
    except Exception as e:
        return "Unknown"

# Function to process the query
def process_query(query):
    # Настройка ChromeOptions для undetected_chromedriver
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument(f"user-agent={user_agent}")
    driver = uc.Chrome(options=chrome_options)

    try:
        # Используем undetected_chromedriver для обхода блокировок
        driver = uc.Chrome(options=chrome_options)

        # Открываем целевую страницу (например, страницу с запросами)
        driver.get("https://chatgpt.com")
        time.sleep(2)

        # Обработка кнопки "Rester déconnecté" или "Stay logged out"
        try:
            WebDriverWait(driver, 1).until(
                lambda d: any(
                    btn.text.strip().lower() in ['rester déconnecté', 'stay logged out']
                    for btn in d.find_elements(By.TAG_NAME, "button")
                )
            )
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.text.strip().lower() in ['rester déconnecté', 'stay logged out']:
                    print("Попап с 'Rester déconnecté' или 'Stay logged out' обнаружен. Клик на кнопку.")
                    btn.click()
                    time.sleep(2)
                    break
        except Exception:
            print("Попап с 'Rester déconnecté' или 'Stay logged out' не найден.")

        # Логика повторных попыток для кнопки поиска
        attempts = 3
        while attempts > 0:
            try:
                search_button = driver.find_element(By.XPATH,
                                                    "//button[@aria-label='Rechercher' or @aria-label='Search']")
                # Прокручиваем страницу, чтобы кнопка стала видимой
                driver.execute_script("arguments[0].scrollIntoView();", search_button)
                time.sleep(1)

                # Пробуем кликнуть по кнопке
                search_button.click()
                time.sleep(2)
                break
            except NoSuchElementException:
                print(f"Кнопка поиска не найдена, повторная попытка ({4 - attempts}/3)")
                attempts -= 1
                time.sleep(2)
            except Exception as e:
                print(f"Ошибка при попытке кликнуть: {e}")
                attempts -= 1
                time.sleep(2)

        if attempts == 0:
            print("Ошибка: не удалось найти кнопку поиска после 3 попыток.")
            return

        # Вводим запрос в текстовое поле и отправляем его
        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "prompt-textarea"))
        )
        textarea.clear()
        textarea.send_keys(query)

        send_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@aria-label='Envoyer le prompt' or @aria-label='Send prompt']"))
        )
        time.sleep(1)
        send_button.click()
        time.sleep(20)

        # Извлекаем текст ответа и ссылки
        response_container = driver.find_element(By.CLASS_NAME, "markdown.prose.w-full.break-words")
        response_text = response_container.text
        response_html = response_container.get_attribute("outerHTML")
        links = extract_links(response_html)

        result = {
            'query': query,
            'answer': response_text,
            'answer_html': response_html,
            'links': links
        }
    finally:
        driver.quit()

    return result

@app.get("/process_query/")
async def process_query_endpoint(query: str):
    try:
        result = process_query(query)
        sentiment = get_sentiment(result['answer'])  # Analyze sentiment based on the result
        result['sentiment'] = sentiment
        return {"queries_data": [result]}
    except WebDriverException as e:
        raise HTTPException(status_code=500, detail=f"Error with Selenium: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Optionally, for debugging:
@app.get("/")
async def read_root():
    return {"message": "FastAPI service is running"}
