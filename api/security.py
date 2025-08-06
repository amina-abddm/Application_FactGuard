import os
from dotenv import load_dotenv

NEWS_API_KEY=e9baebaeb14c471881db9f362e4a4885

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")