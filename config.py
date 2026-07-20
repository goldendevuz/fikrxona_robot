from decouple import config

BOT_TOKEN = config("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in config("ADMIN_IDS").split(",")]
DB_NAME = config("DB_NAME")
