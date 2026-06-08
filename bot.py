import telebot
import requests
from datetime import datetime

TOKEN = '8806120226:AAHePHRmhf_-k6UVkd3TocXrOeyyvaUCX1U'

bot = telebot.TeleBot(TOKEN)

def get_binance_data(symbol):
    """Получает данные с Binance через публичное зеркало"""
    try:
        # Используем зеркало Binance (обходит блокировки)
        url = f"https://api1.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        
        if resp.status_code == 200:
            data = resp.json()
            return {
                'price': float(data['lastPrice']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice'])
            }
    except:
        pass
    
    # Запасной вариант через другую зеркало
    try:
        url = f"https://api3.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        
        if resp.status_code == 200:
            data = resp.json()
            return {
                'price': float(data['lastPrice']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice'])
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

@bot.message_handler(commands=['analyz'])
def analyz_cmd(message):
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    coins = {
        'BTCUSDT': 'Bitcoin',
        'ETHUSDT': 'Ethereum',
        'TONUSDT': 'Toncoin',
        'SOLUSDT': 'Solana'
    }
    
    result = f"🔮 ПРОГНОЗ НА 12 ЧАСОВ\n🕐 {now}\n\n"
    
    for symbol, name in coins.items():
        data = get_binance_data(symbol)
        if data:
            forecast = get_forecast(data['price'], data['high'], data['low'])
            result += f"{name}\n"
            result += f"Текущая: ${data['price']:,.2f}\n"
            result += f"Мин (24ч): ${data['low']:,.2f}\n"
            result += f"Макс (24ч): ${data['high']:,.2f}\n"
            result += f"Прогноз: {forecast}\n\n"
        else:
            result += f"{name}: ошибка получения данных\n\n"
    
    result += "⚠️ Прогноз основан на техническом анализе и не является гарантией."
    bot.reply_to(message, result)

@bot.message_handler(commands=['start', 'check'])
def check_cmd(message):
    bot.reply_to(message, "Привет! Используй команду /analyz для прогноза криптовалют.")

print("✅ Бот запущен! Используй /analyz")
bot.infinity_polling()
