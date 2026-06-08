import telebot
import requests
from datetime import datetime

TOKEN = '8806120226:AAHePHRmhf_-k6UVkd3TocXrOeyyvaUCX1U'

bot = telebot.TeleBot(TOKEN)

def get_crypto():
    try:
        symbols = {
            'BTCUSDT': 'Bitcoin',
            'ETHUSDT': 'Ethereum', 
            'TONUSDT': 'Toncoin',
            'SOLUSDT': 'Solana'
        }
        result = "🪙 Криптовалюты (к USD):\n"
        
        for symbol, name in symbols.items():
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                result += f"{name}: ${price:,.2f}\n"
            else:
                result += f"{name}: ошибка API\n"
                
        return result
    except Exception as e:
        return f"Криптовалюты: ошибка"

def get_currency():
    try:
        url_usd = "https://api.nbrb.by/exrates/rates/USD?parammode=2"
        data_usd = requests.get(url_usd, timeout=15).json()
        usd = float(data_usd['Cur_OfficialRate'])
        
        url_eur = "https://api.nbrb.by/exrates/rates/EUR?parammode=2"
        data_eur = requests.get(url_eur, timeout=15).json()
        eur = float(data_eur['Cur_OfficialRate'])
        
        url_rub = "https://api.nbrb.by/exrates/rates/RUB?parammode=2"
        data_rub = requests.get(url_rub, timeout=15).json()
        rub_100 = float(data_rub['Cur_OfficialRate'])
        
        return (f"💵 Курсы валют (НБРБ):\n"
                f"USD: {usd:.2f} Br\n"
                f"EUR: {eur:.2f} Br\n"
                f"100 RUB: {rub_100:.4f} Br")
    except Exception as e:
        return f"Курсы валют: ошибка"

@bot.message_handler(commands=['start', 'check'])
def check_cmd(message):
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    msg = f"🕐 {now}\n\n{get_currency()}\n\n{get_crypto()}"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['analyz'])
def analyz_cmd(message):
    msg = (
        "📊 **Анализ рынка**\n\n"
        "🔹 Рынок криптовалют: волатильность высокая\n"
        "🔹 Курсы валют: стабильны\n"
        "🔹 Рекомендация: следите за новостями\n\n"
        "💡 *Не инвестиционный совет*"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

print("✅ Бот запущен и работает!")
print("📍 Доступные команды: /check , /analyz")
bot.infinity_polling()
