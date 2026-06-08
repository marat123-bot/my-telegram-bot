import telebot
import requests
from datetime import datetime

TOKEN = '8806120226:AAHePHRmhf_-k6UVkd3TocXrOeyyvaUCX1U'

bot = telebot.TeleBot(TOKEN)

def get_bingx_data(symbol):
    """Получает данные с BingX API"""
    try:
        # BingX публичный API
        url = f"https://api.bingx.com/api/v1/market/ticker?symbol={symbol}"
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == 0:
                ticker = data['data']
                return {
                    'price': float(ticker['lastPrice']),
                    'high': float(ticker['highPrice']),
                    'low': float(ticker['lowPrice']),
                    'change': float(ticker['priceChangePercent'])
                }
    except:
        pass
    return None

def get_forecast(current, high, low):
    """Рассчитывает прогноз на основе позиции цены"""
    if high == low:
        return "Неопределённость"
    try:
        position = (current - low) / (high - low)
        if position > 0.7:
            return "Вероятен рост 📈"
        elif position < 0.3:
            return "Вероятно снижение 📉"
        else:
            return "Боковое движение ↔️"
    except:
        return "Неопределённость"

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

def get_crypto_prices():
    """Получает текущие цены криптовалют"""
    symbols = {
        'BTC-USDT': 'Bitcoin',
        'ETH-USDT': 'Ethereum',
        'TON-USDT': 'Toncoin',
        'SOL-USDT': 'Solana'
    }
    
    result = {}
    for symbol, name in symbols.items():
        data = get_bingx_data(symbol)
        if data:
            result[name] = data['price']
        else:
            result[name] = None
    return result

@bot.message_handler(commands=['start', 'check'])
def check_cmd(message):
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    # Курсы валют
    currency_msg = get_currency()
    
    # Цены криптовалют
    crypto_prices = get_crypto_prices()
    crypto_msg = "🪙 Криптовалюты (к USD):\n"
    for name, price in crypto_prices.items():
        if price:
            crypto_msg += f"{name}: ${price:,.2f}\n"
        else:
            crypto_msg += f"{name}: ошибка\n"
    
    msg = f"🕐 {now}\n\n{currency_msg}\n\n{crypto_msg}"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['analyz'])
def analyz_cmd(message):
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    symbols = {
        'BTC-USDT': 'Bitcoin',
        'ETH-USDT': 'Ethereum',
        'TON-USDT': 'Toncoin',
        'SOL-USDT': 'Solana'
    }
    
    msg = f"🔮 ПРОГНОЗ НА 12 ЧАСОВ\n🕐 {now}\n\n"
    
    for symbol, name in symbols.items():
        data = get_bingx_data(symbol)
        if data:
            forecast = get_forecast(data['price'], data['high'], data['low'])
            msg += f"{name}\n"
            msg += f"Текущая: ${data['price']:,.2f}\n"
            msg += f"Мин (24ч): ${data['low']:,.2f}\n"
            msg += f"Макс (24ч): ${data['high']:,.2f}\n"
            msg += f"Изменение 24ч: {data['change']:+.2f}%\n"
            msg += f"Прогноз: {forecast}\n\n"
        else:
            msg += f"{name}: ошибка получения данных\n\n"
    
    msg += "⚠️ Прогноз основан на техническом анализе и не является гарантией."
    bot.reply_to(message, msg)

print("✅ Бот запущен на BingX API!")
print("📍 /check - курсы валют и криптовалют")
print("📍 /analyz - прогноз на 12 часов")
bot.infinity_polling()
