import telebot
import requests
import threading
import time
import json
import os
from datetime import datetime, timedelta, timezone

# ==================== НАСТРОЙКИ ====================
TOKEN = '8701033549:AAH-8VMkO2TX0KKcirm0nbO5OTSiWwGghPA'
CHAT_ID = 1982505441

bot = telebot.TeleBot(TOKEN)
MSK = timezone(timedelta(hours=3))

USER_DATA_FILE = 'user_data.json'

# ==================== РАБОТА С ДАННЫМИ ====================
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

user_data = load_user_data()
active_trades = {}
temp_data = {}

def get_user_balance(user_id):
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {'balance': 10000, 'positions': [], 'history': []}
        save_user_data(user_data)
    return user_data[str(user_id)]['balance']

def update_user_balance(user_id, amount):
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {'balance': 10000, 'positions': [], 'history': []}
    user_data[str(user_id)]['balance'] += amount
    save_user_data(user_data)

def get_user_positions(user_id):
    if str(user_id) not in user_data:
        return []
    return user_data[str(user_id)].get('positions', [])

def add_position(user_id, symbol, side, amount, entry_price, leverage):
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {'balance': 10000, 'positions': [], 'history': []}
    user_data[str(user_id)]['positions'].append({
        'symbol': symbol,
        'side': side,
        'amount': amount,
        'entry_price': entry_price,
        'leverage': leverage,
        'timestamp': datetime.now(MSK).isoformat()
    })
    save_user_data(user_data)

def remove_position(user_id, index):
    if str(user_id) in user_data and index < len(user_data[str(user_id)]['positions']):
        pos = user_data[str(user_id)]['positions'].pop(index)
        save_user_data(user_data)
        return pos
    return None

def add_to_history(user_id, trade):
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {'balance': 10000, 'positions': [], 'history': []}
    user_data[str(user_id)]['history'].append(trade)
    save_user_data(user_data)

# ==================== РАБОТА С API ====================
def get_current_price(symbol):
    try:
        url = f"https://api.mexc.com/api/v3/ticker/price?symbol={symbol}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return float(resp.json()['price'])
    except:
        pass
    return None

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
        return (f"💵 Курсы валют (НБРБ):\nUSD: {usd:.2f} Br\nEUR: {eur:.2f} Br\n100 RUB: {rub_100:.4f} Br")
    except:
        return "Курсы валют: ошибка"

COMMISSION = 0.00075

def calculate_pnl(side, amount, entry_price, current_price, leverage):
    position_size = amount * leverage
    if side == 'long':
        pnl = (current_price - entry_price) / entry_price * position_size
    else:
        pnl = (entry_price - current_price) / entry_price * position_size
    commission_paid = position_size * COMMISSION * 2
    return pnl - commission_paid

def calculate_liquidation_price(side, entry_price, leverage):
    if side == 'long':
        return entry_price * (1 - 0.95 / leverage)
    else:
        return entry_price * (1 + 0.95 / leverage)

def get_now():
    return datetime.now(MSK)

# ==================== МЕНЮ ====================
def set_commands():
    commands = [
        telebot.types.BotCommand("start", "🏠 Главное меню"),
        telebot.types.BotCommand("quick", "🚀 Быстрая сделка"),
        telebot.types.BotCommand("balance", "💰 Мой баланс"),
        telebot.types.BotCommand("history", "📜 История сделок"),
        telebot.types.BotCommand("analyz", "🔮 Прогноз на 12 часов"),
        telebot.types.BotCommand("check", "📊 Курсы валют и крипты")
    ]
    bot.set_my_commands(commands)
    print("✅ Меню команд установлено")

try:
    bot.remove_webhook()
except:
    pass

# ==================== КОМАНДЫ ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    
    msg = f"""🎮 *Добро пожаловать в Тренировочный Трейдинг!*

💰 *Ваш баланс:* *${balance:,.2f}*
💡 *Стартовый баланс:* $10,000

⚡ *Доступные плечи:* 1x, 10x, 25x, 50x, 75x, 100x, 250x

📚 *Команды:*
• `/quick` - открыть сделку с кнопками
• `/balance` - проверить баланс
• `/history` - история сделок
• `/analyz` - прогноз на 12 часов
• `/check` - курсы валют и криптовалют

🎓 *Совет:* Начните с маленьких сумм!"""
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🚀 Начать сделку", callback_data="new_trade"))
    
    bot.reply_to(message, msg, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['quick'])
def quick_trade(message):
    bot.delete_message(message.chat.id, message.message_id)
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        telebot.types.InlineKeyboardButton("₿ BTC", callback_data="coin_BTC"),
        telebot.types.InlineKeyboardButton("⟠ ETH", callback_data="coin_ETH"),
        telebot.types.InlineKeyboardButton("⚡ TON", callback_data="coin_TON"),
        telebot.types.InlineKeyboardButton("◎ SOL", callback_data="coin_SOL")
    ]
    markup.add(*buttons)
    
    msg = bot.send_message(message.chat.id, "📊 *Выберите монету:*", reply_markup=markup, parse_mode='Markdown')
    temp_data[str(message.chat.id)] = {'msg_id': msg.message_id}

@bot.message_handler(commands=['balance'])
def balance_cmd(message):
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    positions = get_user_positions(user_id)
    total_pnl = 0
    
    for pos in positions:
        price = get_current_price(pos['symbol'] + 'USDT')
        if price:
            pnl = calculate_pnl(pos['side'], pos['amount'], pos['entry_price'], price, pos['leverage'])
            total_pnl += pnl
    
    msg = f"💰 *ВАШ БАЛАНС*\n\n"
    msg += f"Свободно: *${balance:,.2f}*\n"
    
    if positions:
        msg += f"\n📊 *Открытые позиции:* {len(positions)}\n"
        msg += f"Текущий PnL: *{total_pnl:+.2f}* USDT\n"
        msg += f"Общая стоимость: *${balance + total_pnl:,.2f}*\n"
    else:
        msg += f"\n📭 Открытых позиций нет\n"
    
    msg += f"\n💡 *Стартовый баланс:* $10,000"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🚀 Новая сделка", callback_data="new_trade"))
    
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['history'])
def history_cmd(message):
    user_id = message.from_user.id
    if str(user_id) not in user_data:
        bot.reply_to(message, "📭 У вас пока нет истории сделок")
        return
    
    history = user_data[str(user_id)].get('history', [])
    if not history:
        bot.reply_to(message, "📭 У вас пока нет завершённых сделок")
        return
    
    msg = "📜 *ИСТОРИЯ СДЕЛОК (последние 10)*\n\n"
    for trade in history[-10:]:
        emoji = "✅" if trade['pnl'] > 0 else "❌"
        msg += f"{emoji} *{trade['symbol']}* | {trade.get('leverage', 1)}x | ${trade['amount']:,.2f}\n"
        msg += f"   PnL: {trade['pnl']:+.2f} USDT\n"
        if 'balance_before' in trade:
            msg += f"   Баланс: ${trade['balance_before']:,.2f} → ${trade['balance_after']:,.2f}\n"
        msg += "\n"
    
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.message_handler(commands=['analyz'])
def analyz_cmd(message):
    now = get_now().strftime('%d.%m.%Y %H:%M')
    symbols = {'BTCUSDT': 'Bitcoin', 'ETHUSDT': 'Ethereum', 'TONUSDT': 'Toncoin', 'SOLUSDT': 'Solana'}
    
    result = f"🔮 ПРОГНОЗ НА 12 ЧАСОВ\n🕐 {now}\n\n"
    
    for symbol, name in symbols.items():
        data = get_mexc_data(symbol)
        if data:
            position = (data['price'] - data['low']) / (data['high'] - data['low']) if data['high'] != data['low'] else 0.5
            if position > 0.7:
                forecast = "Вероятен рост 📈"
            elif position < 0.3:
                forecast = "Вероятно снижение 📉"
            else:
                forecast = "Боковое движение ↔️"
            
            result += f"{name}\n"
            result += f"Текущая: ${data['price']:,.2f}\n"
            result += f"Мин (24ч): ${data['low']:,.2f}\n"
            result += f"Макс (24ч): ${data['high']:,.2f}\n"
            result += f"Изменение 24ч: {data['change']:+.2f}%\n"
            result += f"Прогноз: {forecast}\n\n"
        else:
            result += f"{name}: ошибка получения данных\n\n"
    
    result += "⚠️ Прогноз основан на техническом анализе и не является гарантией."
    bot.reply_to(message, result, parse_mode='Markdown')

@bot.message_handler(commands=['check'])
def check_cmd(message):
    now = get_now().strftime('%d.%m.%Y %H:%M')
    symbols = {'BTCUSDT': 'Bitcoin', 'ETHUSDT': 'Ethereum', 'TONUSDT': 'Toncoin', 'SOLUSDT': 'Solana'}
    crypto_msg = "🪙 Криптовалюты (к USD):\n"
    for symbol, name in symbols.items():
        data = get_mexc_data(symbol)
        if data:
            crypto_msg += f"{name}: ${data['price']:,.2f}\n"
        else:
            crypto_msg += f"{name}: ошибка\n"
    msg = f"🕐 {now}\n\n{get_currency()}\n\n{crypto_msg}"
    bot.reply_to(message, msg)

# ==================== КОЛБЭКИ ====================
@bot.callback_query_handler(func=lambda call: call.data.startswith('coin_'))
def select_leverage(call):
    coin = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    leverages = [1, 10, 25, 50, 75, 100, 250]
    buttons = [telebot.types.InlineKeyboardButton(f"{lev}x", callback_data=f"lev_{coin}_{lev}") for lev in leverages]
    markup.add(*buttons)
    
    msg = bot.send_message(call.message.chat.id, f"📊 *{coin}*\n\nВыберите плечо:", reply_markup=markup, parse_mode='Markdown')
    temp_data[str(call.message.chat.id)] = {'coin': coin, 'msg_id': msg.message_id}

@bot.callback_query_handler(func=lambda call: call.data.startswith('lev_'))
def ask_amount(call):
    _, coin, leverage = call.data.split('_')
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    msg = bot.send_message(call.message.chat.id, f"📊 *{coin} | Плечо {leverage}x*\n\n💰 Введите сумму сделки (min $10, max ${get_user_balance(call.from_user.id):,.2f}):", parse_mode='Markdown')
    
    temp_data[str(call.message.chat.id)] = {
        'coin': coin,
        'leverage': int(leverage),
        'msg_id': msg.message_id
    }
    bot.register_next_step_handler(msg, process_trade_amount)

@bot.callback_query_handler(func=lambda call: call.data == 'new_trade')
def new_trade(call):
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        telebot.types.InlineKeyboardButton("₿ BTC", callback_data="coin_BTC"),
        telebot.types.InlineKeyboardButton("⟠ ETH", callback_data="coin_ETH"),
        telebot.types.InlineKeyboardButton("⚡ TON", callback_data="coin_TON"),
        telebot.types.InlineKeyboardButton("◎ SOL", callback_data="coin_SOL")
    ]
    markup.add(*buttons)
    
    bot.send_message(call.message.chat.id, "📊 *Выберите монету:*", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'show_balance')
def show_balance(call):
    user_id = call.from_user.id
    balance = get_user_balance(user_id)
    positions = get_user_positions(user_id)
    total_pnl = 0
    
    for pos in positions:
        price = get_current_price(pos['symbol'] + 'USDT')
        if price:
            pnl = calculate_pnl(pos['side'], pos['amount'], pos['entry_price'], price, pos['leverage'])
            total_pnl += pnl
    
    msg = f"💰 *ВАШ БАЛАНС*\n\n"
    msg += f"Свободно: *${balance:,.2f}*\n"
    
    if positions:
        msg += f"\n📊 Открыто позиций: {len(positions)}\n"
        msg += f"Текущий PnL: *{total_pnl:+.2f}* USDT\n"
        msg += f"Общая стоимость: *${balance + total_pnl:,.2f}*\n"
    else:
        msg += f"\n📭 Открытых позиций нет\n"
    
    msg += f"\n💡 Стартовый баланс: *$10,000*"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🚀 Новая сделка", callback_data="new_trade"))
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('close_'))
def close_trade(call):
    parts = call.data.split('_')
    if len(parts) < 5:
        bot.answer_callback_query(call.id, "Ошибка: неверные данные сделки")
        return
    
    coin = parts[1]
    amount = float(parts[2])
    leverage = int(parts[3])
    entry_price = float(parts[4])
    user_id = call.from_user.id
    
    bot.answer_callback_query(call.id)
    
    if str(call.message.chat.id) in active_trades:
        del active_trades[str(call.message.chat.id)]
    
    current_price = get_current_price(f"{coin}USDT")
    if not current_price:
        current_price = entry_price
    
    pnl = calculate_pnl('long', amount, entry_price, current_price, leverage)
    old_balance = get_user_balance(user_id)
    update_user_balance(user_id, amount + pnl)
    new_balance = get_user_balance(user_id)
    
    trade = {
        'symbol': coin,
        'side': 'long',
        'amount': amount,
        'leverage': leverage,
        'entry_price': entry_price,
        'exit_price': current_price,
        'pnl': pnl,
        'balance_before': old_balance,
        'balance_after': new_balance,
        'timestamp': get_now().isoformat()
    }
    add_to_history(user_id, trade)
    
    emoji = "🎉" if pnl > 0 else "😢" if pnl < 0 else "🤝"
    result_msg = f"{emoji} *СДЕЛКА ЗАКРЫТА* {emoji}\n\n"
    result_msg += f"📊 {coin} | {leverage}x | ${amount:,.2f}\n"
    result_msg += f"💰 Результат: *{pnl:+.2f} USDT*\n\n"
    result_msg += f"📈 Баланс до: *${old_balance:,.2f}*\n"
    result_msg += f"📉 Баланс после: *${new_balance:,.2f}*\n\n"
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("💰 Баланс", callback_data="show_balance"),
        telebot.types.InlineKeyboardButton("🚀 Новая сделка", callback_data="new_trade")
    )
    
    bot.edit_message_text(result_msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

# ==================== ОБРАБОТКА СУММЫ ====================
def process_trade_amount(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    data = temp_data.get(str(chat_id), {})
    if not data:
        bot.send_message(chat_id, "❌ Сессия истекла. Начните заново с /quick")
        return
    
    coin = data.get('coin')
    leverage = data.get('leverage')
    
    bot.delete_message(chat_id, data.get('msg_id'))
    bot.delete_message(chat_id, message.message_id)
    
    try:
        amount = float(message.text.strip())
    except:
        bot.send_message(chat_id, "❌ Введите число!\nНачните заново с /quick")
        del temp_data[str(chat_id)]
        return
    
    balance = get_user_balance(user_id)
    
    if amount < 10:
        bot.send_message(chat_id, "❌ Минимальная сумма: $10\nНачните заново с /quick")
        del temp_data[str(chat_id)]
        return
    
    if amount > balance:
        bot.send_message(chat_id, f"❌ Недостаточно средств! Ваш баланс: ${balance:,.2f}\nНачните заново с /quick")
        del temp_data[str(chat_id)]
        return
    
    current_price = get_current_price(f"{coin}USDT")
    if not current_price:
        bot.send_message(chat_id, "❌ Не удалось получить цену. Попробуйте позже.\nНачните заново с /quick")
        del temp_data[str(chat_id)]
        return
    
    side = 'long'
    position_size = amount * leverage
    liquidation_price = calculate_liquidation_price(side, current_price, leverage)
    
    update_user_balance(user_id, -amount)
    add_position(user_id, coin, side, amount, current_price, leverage)
    
    trade_msg = f"📊 *АКТИВНАЯ СДЕЛКА*\n\n"
    trade_msg += f"Монета: *{coin}*\n"
    trade_msg += f"Плечо: *{leverage}x*\n"
    trade_msg += f"Сумма: *${amount:,.2f}*\n"
    trade_msg += f"Размер позиции: *${position_size:,.2f}*\n"
    trade_msg += f"Цена входа: *${current_price:.2f}*\n"
    trade_msg += f"Цена ликвидации: *${liquidation_price:.2f}*\n"
    trade_msg += f"Баланс: *${get_user_balance(user_id):,.2f}*\n\n"
    trade_msg += f"📈 *Текущий P/L обновляется автоматически* 📉"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("❌ ЗАКРЫТЬ СДЕЛКУ", callback_data=f"close_{coin}_{amount}_{leverage}_{current_price}"))
    
    sent_msg = bot.send_message(chat_id, trade_msg, reply_markup=markup, parse_mode='Markdown')
    
    active_trades[str(chat_id)] = {
        'coin': coin,
        'amount': amount,
        'leverage': leverage,
        'entry_price': current_price,
        'message_id': sent_msg.message_id,
        'user_id': user_id
    }
    
    start_pl_updater(chat_id)
    del temp_data[str(chat_id)]

# ==================== ОБНОВЛЕНИЕ P/L ====================
def start_pl_updater(chat_id):
    def update_pl():
        while str(chat_id) in active_trades:
            trade = active_trades.get(str(chat_id))
            if not trade:
                break
            
            coin = trade['coin']
            amount = trade['amount']
            leverage = trade['leverage']
            entry_price = trade['entry_price']
            user_id = trade['user_id']
            
            current_price = get_current_price(f"{coin}USDT")
            if current_price:
                pnl = calculate_pnl('long', amount, entry_price, current_price, leverage)
                emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                
                try:
                    position_size = amount * leverage
                    liquidation_price = calculate_liquidation_price('long', entry_price, leverage)
                    
                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.add(telebot.types.InlineKeyboardButton("❌ ЗАКРЫТЬ СДЕЛКУ", callback_data=f"close_{coin}_{amount}_{leverage}_{entry_price}"))
                    
                    new_msg = f"📊 *АКТИВНАЯ СДЕЛКА*\n\n"
                    new_msg += f"Монета: *{coin}*\n"
                    new_msg += f"Плечо: *{leverage}x*\n"
                    new_msg += f"Сумма: *${amount:,.2f}*\n"
                    new_msg += f"Размер позиции: *${position_size:,.2f}*\n"
                    new_msg += f"Цена входа: *${entry_price:.2f}*\n"
                    new_msg += f"Текущая цена: *${current_price:.2f}*\n"
                    new_msg += f"Цена ликвидации: *${liquidation_price:.2f}*\n"
                    new_msg += f"{emoji} *P/L: {pnl:+.2f} USDT* {emoji}\n\n"
                    new_msg += f"💰 Баланс: *${get_user_balance(user_id):,.2f}*"
                    
                    bot.edit_message_text(new_msg, chat_id, trade['message_id'], reply_markup=markup, parse_mode='Markdown')
                except:
                    pass
            
            time.sleep(3)
    
    threading.Thread(target=update_pl, daemon=True).start()

# ==================== ЗАПУСК ====================
set_commands()
print("✅ Бот запущен!")
print("🎮 Команды: /start, /quick, /balance, /history, /analyz, /check")
bot.infinity_polling()
