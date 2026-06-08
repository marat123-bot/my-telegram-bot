import telebot
import requests
from datetime import datetime

TOKEN = '8806120226:AAHePHRmhf_-k6UVkd3TocXrOeyyvaUCX1U'

bot = telebot.TeleBot(TOKEN)

def get_crypto():
    try:
        symbols = ['BTCUSDT', 'ETHUSDT', 'TONUSDT', 'SOLUSDT']
        names = {'BTCUSDT': 'Bitcoin', 'ETHUSDT': 'Ethereum', 'TONUSDT': 'Toncoin', 'SOLUSDT': 'Solana'}
        result = "Криптовалюты (к USD):\n"
        for sym in symbols:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={sym}"
            data = requests.get(url, timeout=10).json()
            price = float(data['price'])
            result += f"{names[sym]}: ${price:,.2f}\n"
        return result
    except:
        return "Криптовалюты: ошибка"

def get_currency():
    try:
        url_rub = "https://api.nbrb.by/exrates/rates/RUB?parammode=2"
        data_rub = requests.get(url_rub, timeout=15).json()
        rub_100 = float(data_rub['Cur_OfficialRate'])
        
        url_usd = "https://api.nbrb.by/exrates/rates/USD?parammode=2"
        data_usd = requests.get(url_usd, timeout=15).json()
        usd = float(data_usd['Cur_OfficialRate'])
        
        url_eur = "https://api.nbrb.by/exrates/rates/EUR?parammode=2"
        data_eur = requests.get(url_eur, timeout=15).json()
        eur = float(data_eur['Cur_OfficialRate'])
        
        return (f"Курсы валют (НБРБ):\n"
                f"USD: {usd:.2f} Br\n"
                f"EUR: {eur:.2f} Br\n"
                f"100 RUB: {rub_100:.4f} Br")
    except:
        return "Курсы валют: ошибка"

@bot.message_handler(commands=['start', 'check'])
def check_cmd(message):
    msg = f"{datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n{get_currency()}\n\n{get_crypto()}"
    bot.reply_to(message, msg)

print("Бот запущен!")
bot.infinity_polling()
