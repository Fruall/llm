import time
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "FastAPI server is running"}

@app.get("/process_query/")
async def process_query(query: str):
    # Настройка Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск без графического интерфейса
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Открытие страницы по запросу
        driver.get(query)

        # Получение содержимого тега <title>
        page_title = driver.title

        # Возвращаем результат
        return {"page_title": page_title}

    finally:
        driver.quit()  # Закрытие браузера после выполнения запроса
