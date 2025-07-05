import os
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


secret_key = os.environ.get('SECRET_KEY') or ""
db_host = os.environ.get('DB_HOST') or ""
db_port = os.environ.get('DB_PORT') or ""
db_name = os.environ.get('DB_NAME') or ""
url = os.environ.get('URL') or ""
bot_token = os.environ.get('BOT_TOKEN') or ""
