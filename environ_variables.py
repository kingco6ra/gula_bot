import os

from dotenv import load_dotenv

load_dotenv('.env')
API_KEY = os.environ['API_KEY']
TELEBOT_TOKEN = os.environ['TELEBOT_TOKEN']
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
