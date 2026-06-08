import telebot
import requests
from datetime import datetime

TOKEN = '8806120226:AAHePHRmhf_-k6UVkd3TocXrOeyyvaUCX1U'

bot = telebot.TeleBot(TOKEN)

def get_crypto_data():
    """Получает данные криптовалют с CoinGecko"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,the-open-network,solana&vs_currencies=usd&include_24hr_change=true&include_24hr_high=true&include_24hr_low=true"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        # Маппинг ID на названия
        mapping = {
            'bitcoin': 'Bitcoin',
            'ethereum': 'Ethereum',
            'the-open-network': 'Toncoin',
            'solana': 'Solana'
        }
        
        result = {}
        for coin_id, name in mapping.items():
            if coin_id in data:
                result[name] = {
                    'price': data[coin_id]['usd'],
                    'high': data[coin_id].get('usd_24h_high', data[coin_id]['usd']),
                    'low': data[coin_id].get('usd_24h_low', data[coin_id]['usd']),
                    'change': data[coin_id].get('usd_24h_change', 0)
                }
            else:
                result[name] = None
        return result
    except Exception as e:
        print(f"Ошибка CoinGecko: {e}")
        return None

def get_forecast(current, high, low):
    """Простой прогноз"""
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

def get_crypto():
    """Краткая информация по криптовалютам"""
    data = get_crypto_data()
    if not data:
        return "🪙 Криптовалюты: временно недоступны\n"
    
    result = "🪙 Криптовалюты (к USD):\n"
    for name, info in data.items():
        if info:
            result += f"{name}: ${info['price']:,.2f}\n"
        else:
            result += f"{name}: ошибка\n"
    return result

def get_full_forecast():
    """Полный прогноз"""
    data = get_crypto_data()
    if not data:
        return "🔮 Прогноз временно недоступен\n"
    
    result = "🔮 ПРОГНОЗ НА 12 ЧАСОВ\n\n"
    
    for name, info in data.items():
        if info:
            current = info['price']
            high = info['high']
            low = info['low']
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
    except Exception as e:
        return f"Курсы валют: ошибка"

@bot.message_handler(commands=['start', 'check'])
def check_cmd(message):
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    msg = f"🕐 {now}\n\n{get_currency()}\n\n{get_crypto()}"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['analyz'])
def analyz_cmd(message):
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    msg = f"🕐 {now}\n\n{get_currency()}\n\n{get_crypto()}\n\n{get_full_forecast()}"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['forecast'])
def forecast_cmd(message):
    msg = get_full_forecast()
    bot.reply_to(message, msg)

print("✅ Бот запущен на CoinGecko API!")
print("📍 Команды: /check, /analyz, /forecast")
bot.infinity_polling()
