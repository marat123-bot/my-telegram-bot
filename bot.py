import telebot
import requests
from datetime import datetime

TOKEN = '8806120226:AAHePHRmhf_-k6UVkd3TocXrOeyyvaUCX1U'

bot = telebot.TeleBot(TOKEN)

def get_crypto_prices():
    """Получает текущие цены криптовалют с CoinCap"""
    coins = {
        'bitcoin': 'Bitcoin',
        'ethereum': 'Ethereum',
        'the-open-network': 'Toncoin',
        'solana': 'Solana'
    }
    
    result = {}
    for coin_id, name in coins.items():
        try:
            url = f"https://api.coincap.io/v2/assets/{coin_id}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if 'data' in data:
                result[name] = float(data['data']['priceUsd'])
        except:
            result[name] = None
    return result

def get_forecast_data():
    """Получает данные для прогноза"""
    coins = {
        'bitcoin': 'Bitcoin',
        'ethereum': 'Ethereum',
        'the-open-network': 'Toncoin',
        'solana': 'Solana'
    }
    
    result = {}
    for coin_id, name in coins.items():
        try:
            url = f"https://api.coincap.io/v2/assets/{coin_id}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if 'data' in data:
                result[name] = {
                    'price': float(data['data']['priceUsd']),
                    'change': float(data['data']['changePercent24Hr'])
                }
        except:
            result[name] = None
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
    
    # Получаем курсы валют
    currency_msg = get_currency()
    
    # Получаем цены криптовалют
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
    
    forecast_data = get_forecast_data()
    
    msg = f"🔮 ПРОГНОЗ НА 12 ЧАСОВ\n🕐 {now}\n\n"
    
    for name, data in forecast_data.items():
        if data:
            change = data['change']
            price = data['price']
            
            # Прогноз на основе изменения за 24 часа
            if change > 3:
                forecast = "Вероятен рост 📈"
            elif change < -3:
                forecast = "Вероятно снижение 📉"
            else:
                forecast = "Боковое движение ↔️"
            
            msg += f"{name}\n"
            msg += f"Текущая: ${price:,.2f}\n"
            msg += f"24h изменение: {change:+.2f}%\n"
            msg += f"Прогноз: {forecast}\n\n"
        else:
            msg += f"{name}: ошибка получения данных\n\n"
    
    msg += "⚠️ Прогноз основан на техническом анализе и не является гарантией."
    bot.reply_to(message, msg)

print("✅ Бот запущен!")
print("📍 /check - курсы валют и криптовалют")
print("📍 /analyz - прогноз на 12 часов")
bot.infinity_polling()
