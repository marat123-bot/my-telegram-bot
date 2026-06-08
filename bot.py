import telebot
import requests
from datetime import datetime

TOKEN = '8806120226:AAHePHRmhf_-k6UVkd3TocXrOeyyvaUCX1U'

bot = telebot.TeleBot(TOKEN)

def get_crypto_price(symbol):
    """Получает цену криптовалюты с Bybit"""
    try:
        url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['retCode'] == 0:
            return float(data['result']['list'][0]['lastPrice'])
    except:
        pass
    return None

def get_crypto_24h(symbol):
    """Получает мин/макс за 24ч с Bybit"""
    try:
        url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['retCode'] == 0:
            ticker = data['result']['list'][0]
            return {
                'high': float(ticker['highPrice24h']),
                'low': float(ticker['lowPrice24h']),
                'last': float(ticker['lastPrice'])
            }
    except:
        pass
    return None

def get_forecast(current, high, low):
    """Простой прогноз на основе позиции цены в диапазоне"""
    if high == low:
        return "Неопределённость"
    position = (current - low) / (high - low)
    if position > 0.7:
        return "Вероятен рост 📈"
    elif position < 0.3:
        return "Вероятно снижение 📉"
    else:
        return "Боковое движение ↔️"

def get_crypto():
    """Получает данные по всем криптовалютам"""
    symbols = {
        'BTCUSDT': 'Bitcoin',
        'ETHUSDT': 'Ethereum',
        'TONUSDT': 'Toncoin',
        'SOLUSDT': 'Solana'
    }
    
    result = "🪙 Криптовалюты (к USD):\n"
    for symbol, name in symbols.items():
        price = get_crypto_price(symbol)
        if price:
            result += f"{name}: ${price:,.2f}\n"
        else:
            result += f"{name}: ошибка\n"
    return result

def get_forecast_text():
    """Получает полный прогноз на 12 часов"""
    symbols = {
        'BTCUSDT': 'Bitcoin',
        'ETHUSDT': 'Ethereum',
        'TONUSDT': 'Toncoin',
        'SOLUSDT': 'Solana'
    }
    
    result = "🔮 ПРОГНОЗ НА 12 ЧАСОВ\n\n"
    
    for symbol, name in symbols.items():
        data = get_crypto_24h(symbol)
        if data:
            current = data['last']
            high = data['high']
            low = data['low']
            forecast = get_forecast(current, high, low)
            
            result += f"{name}\n"
            result += f"Текущая: ${current:,.2f}\n"
            result += f"Мин (24ч): ${low:,.2f}\n"
            result += f"Макс (24ч): ${high:,.2f}\n"
            result += f"Прогноз: {forecast}\n\n"
        else:
            result += f"{name}: ошибка получения данных\n\n"
    
    result += "⚠️ Прогноз основан на техническом анализе и не является гарантией."
    return result

def get_currency():
    """Курсы валют НБРБ"""
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
    except:
        return "Курсы валют: ошибка"

@bot.message_handler(commands=['start', 'check'])
def check_cmd(message):
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    msg = f"🕐 {now}\n\n{get_currency()}\n\n{get_crypto()}"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['analyz'])
def analyz_cmd(message):
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    msg = f"🕐 {now}\n\n{get_currency()}\n\n{get_crypto()}\n\n{get_forecast_text()}"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['forecast'])
def forecast_cmd(message):
    msg = get_forecast_text()
    bot.reply_to(message, msg)

print("✅ Бот запущен!")
print("📍 Команды: /check - курсы и цены, /analyz - полный анализ, /forecast - только прогноз")
bot.infinity_polling()
