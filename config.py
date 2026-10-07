import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "180"))
LLM_URL = os.getenv("LLM_URL", "https://text.pollinations.ai/openai")
LLM_KEY = os.getenv("LLM_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "openai")

# Заказ проходит, если в названии/описании есть хотя бы одно из этих слов
KEYWORDS = [
    "бот", "telegram", "телеграм", "телеграмм", "сайт", "лендинг", "landing",
    "веб", "web", "парсер", "парсинг", "интернет-магазин", "интернет магазин",
    "верстк", "frontend", "backend", "fullstack", "full stack", "python", "django",
    "flask", "fastapi", "react", "vue", "next.js", "node", "javascript", "mini app",
    "миниапп", "мини-апп", "crm", "api", "автоматизац", "wordpress", "tilda", "битрикс",
]
# Если есть любое из этих слов, заказ пропускается
STOP_WORDS = [
    "логотип", "копирайт", "перевод", "видеомонтаж", "озвучк",
    "swift", "unity", "накрутка",
]
MIN_BUDGET = 0  # в рублях; заказы с указанным бюджетом ниже пропускаются
