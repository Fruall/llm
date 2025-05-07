import time
from fastapi import FastAPI, HTTPException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

app = FastAPI()

@app.get("/process_query/")
async def process_query(query: str):
    # Настройка Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск без графического интерфейса
    chrome_options.add_argument("--disable-dev-shm-usage")  # Отключение ограничений на использование памяти
    chrome_options.add_argument("--no-sandbox")  # Важный флаг для работы на сервере
    chrome_options.add_argument("--remote-debugging-port=9222")  # Порт для отладки
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Открытие страницы по запросу
        driver.get(query)

        # Получение содержимого тега <title>
        page_title = driver.title

        # Возвращаем результат
        return {"page_title": page_title}

    except WebDriverException as e:
        raise HTTPException(status_code=500, detail=f"Error with Selenium: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    finally:
        driver.quit()  # Закрытие браузера после выполнения запроса
