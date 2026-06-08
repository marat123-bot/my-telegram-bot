import telebot
import requests
import threading
import time
from datetime import datetime

TOKEN = '8806120226:AAHePHRmhf_-k6UVkd3TocXrOeyyvaUCX1U'
CHAT_ID = 1982505441

bot = telebot.TeleBot(TOKEN)

# Храним последние цены для отслеживания
last_prices = {
    'Bitcoin': None,
    'Ethereum': None,
    'Toncoin': None,
    'Solana': None
}

def get_mexc_data(symbol):
    try:
        url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={symbol}"
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            data = resp.json()
            return {
                'price': float(data['lastPrice']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice']),
                'change': float(data['priceChangePercent'])
            }
    except:
        pass
    return None

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
    except:
        return "Курсы валют: ошибка"

def get_forecast(current, high, low):
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

def get_full_report():
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    symbols = {'BTCUSDT': 'Bitcoin', 'ETHUSDT': 'Ethereum', 'TONUSDT': 'Toncoin', 'SOLUSDT': 'Solana'}
    
    result = f"📊 ЕЖЕДНЕВНАЯ СВОДКА\n🕐 {now}\n\n"
    result += get_currency()
    result += "\n\n🪙 Криптовалюты:\n"
    
    for symbol, name in symbols.items():
        data = get_mexc_data(symbol)
        if data:
            result += f"\n{name}: ${data['price']:,.2f}\n24h изменение: {data['change']:+.2f}%\n"
        else:
            result += f"\n{name}: ошибка\n"
    
    result += "\n🔮 ПРОГНОЗ НА 12 ЧАСОВ\n\n"
    for symbol, name in symbols.items():
        data = get_mexc_data(symbol)
        if data:
            forecast = get_forecast(data['price'], data['high'], data['low'])
            result += f"{name}\n"
            result += f"Текущая: ${data['price']:,.2f}\n"
            result += f"Мин (24ч): ${data['low']:,.2f}\n"
            result += f"Макс (24ч): ${data['high']:,.2f}\n"
            result += f"Прогноз: {forecast}\n\n"
        else:
            result += f"{name}: ошибка\n\n"
    
    result += "⚠️ Прогноз основан на техническом анализе и не является гарантией."
    return result

def get_hourly_crypto():
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    symbols = {'BTCUSDT': 'Bitcoin', 'ETHUSDT': 'Ethereum', 'TONUSDT': 'Toncoin', 'SOLUSDT': 'Solana'}
    
    result = f"🕐 {now}\n\n💰 ЕЖЕЧАСНАЯ СВОДКА КРИПТОВАЛЮТ\n\n"
    for symbol, name in symbols.items():
        data = get_mexc_data(symbol)
        if data:
            result += f"{name}: ${data['price']:,.2f}\n24h изменение: {data['change']:+.2f}%\n\n"
        else:
            result += f"{name}: ошибка\n\n"
    return result

def check_price_alerts():
    """Проверяет резкие изменения и отправляет только при скачке"""
    global last_prices
    alerts = []
    symbols = {'BTCUSDT': 'Bitcoin', 'ETHUSDT': 'Ethereum', 'TONUSDT': 'Toncoin', 'SOLUSDT': 'Solana'}
    
    for symbol, name in symbols.items():
        data = get_mexc_data(symbol)
        if data:
            current_price = data['price']
            last_price = last_prices.get(name)
            
            if last_price is not None:
                change_percent = ((current_price - last_price) / last_price) * 100
                
                # Оповещение только при изменении более 3%
                if abs(change_percent) >= 3:
                    direction = "РЕЗКИЙ РОСТ 🚀" if change_percent > 0 else "РЕЗКОЕ ПАДЕНИЕ 📉"
                    alerts.append(f"{direction} {name}\n"
                                  f"Изменение: {change_percent:+.2f}%\n"
                                  f"Цена была: ${last_price:,.2f}\n"
                                  f"Цена стала: ${current_price:,.2f}\n"
                                  f"🕐 {datetime.now().strftime('%H:%M:%S')}")
            
            # Обновляем цену
            last_prices[name] = current_price
    
    return alerts

def send_notifications():
    """Фоновая задача для отправки уведомлений"""
    last_daily = None
    last_hourly = None
    last_alert_check = None
    
    while True:
        now = datetime.now()
        current_hour = now.hour
        current_time_str = now.strftime('%H:%M')
        
        # 1. Ежедневные сводки в 00:00 и 12:00
        if current_time_str in ['00:00', '12:00']:
            if last_daily != current_time_str:
                report = get_full_report()
                try:
                    bot.send_message(CHAT_ID, report)
                    last_daily = current_time_str
                    print(f"📨 Отправлена ежедневная сводка в {current_time_str}")
                except Exception as e:
                    print(f"Ошибка: {e}")
        
        # 2. Ежечасные сводки
        if current_time_str.endswith(':00'):
            if last_hourly != current_time_str:
                hourly = get_hourly_crypto()
                try:
                    bot.send_message(CHAT_ID, hourly)
                    last_hourly = current_time_str
                    print(f"📨 Отправлена ежечасная сводка в {current_time_str}")
                except Exception as e:
                    print(f"Ошибка: {e}")
        
        # 3. Проверка резких изменений (каждые 2 минуты, но оповещает ТОЛЬКО при скачке)
        if last_alert_check is None or (datetime.now() - last_alert_check).seconds >= 120:
            alerts = check_price_alerts()
            for alert in alerts:
                try:
                    bot.send_message(CHAT_ID, alert)
                    print(f"⚠️ Резкое изменение: {alert[:50]}...")
                except Exception as e:
                    print(f"Ошибка отправки: {e}")
            last_alert_check = datetime.now()
        
        time.sleep(30)

@bot.message_handler(commands=['start', 'check'])
def check_cmd(message):
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    currency_msg = get_currency()
    symbols = {'BTCUSDT': 'Bitcoin', 'ETHUSDT': 'Ethereum', 'TONUSDT': 'Toncoin', 'SOLUSDT': 'Solana'}
    crypto_msg = "🪙 Криптовалюты (к USD):\n"
    for symbol, name in symbols.items():
        data = get_mexc_data(symbol)
        if data:
            crypto_msg += f"{name}: ${data['price']:,.2f}\n"
        else:
            crypto_msg += f"{name}: ошибка\n"
    msg = f"🕐 {now}\n\n{currency_msg}\n\n{crypto_msg}"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['analyz'])
def analyz_cmd(message):
    msg = get_full_report()
    bot.reply_to(message, msg)

@bot.message_handler(commands=['hourly'])
def hourly_cmd(message):
    msg = get_hourly_crypto()
    bot.reply_to(message, msg)

threading.Thread(target=send_notifications, daemon=True).start()

print("✅ Бот запущен!")
print("📍 /check /analyz /hourly")
print("📨 Уведомления:")
print("   - 00:00 и 12:00 → полная сводка")
print("   - Каждый час → криптовалюты")
print("   - Только при резком скачке цены (>3%) → оповещение")
bot.infinity_polling()
