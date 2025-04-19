from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

# Токен бота
TOKEN = os.getenv("BOT_TOKEN")

# Ключ Spoonacular API
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# Параметры базы данных
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")