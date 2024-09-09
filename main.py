# ======================
# | RECODED BY @vemorr |
# ======================

import re
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types, Dispatcher, Bot, executor
import requests
import string
import random
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
from datetime import datetime
import asyncio
import bet_sender
import os
import kb
import config
import sqlite3
import states

bot = Bot(token=config.TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)

COEFFICIENTS = {
    'победа 1': 1.9,
    'победа 2': 1.9,
    'п1': 1.9,
    'п2': 1.9,
    'ничья': 2.5,
    'нечет': 1.9,
    'фут гол': 1.8,
    'фут мимо': 1.8,
    'баскет гол': 1.8,
    'баскет мимо': 1.8,
    'больше': 1.9,
    'меньше': 1.9,
    'чет': 1.9,
    'дартс белое': 1.8,
    'дартс красное': 1.8,
    'дартс мимо': 1.8,
    'дартс центр': 1.8,
    'камень': 1.9,
    'ножницы': 1.9,
    'бумага': 1.9
}

DICE_CONFIG = {
    'нечет': ("🎲", [1, 3, 5]),
    'фут гол': ("⚽️", [3, 4, 5]),
    'фут мимо': ("⚽️", [1, 2, 6]),
    'баскет гол': ("🏀", [4, 5, 6]),
    'баскет мимо': ("🏀", [1, 2, 3]),
    'больше': ("🎲", [4, 5, 6]),
    'меньше': ("🎲", [1, 2, 3]),
    'чет': ("🎲", [2, 4, 6]),
    'дартс белое': ("🎯", [3, 5]),
    'жартс красное': ("🎯", [2, 4]),
    'дартс мимо': ("🎯", [1]),
    'дартс центр': ("🎯", [6]),
    'сектор 1': ("🎲", [1, 2]),
    'сектор 2': ("🎲", [3, 4]),
    'сектор 3': ("🎲", [3, 4]),
    'плинко': ("🎲", [4, 5, 6]),
    'бумага': ("✋", ['👊']),
    'камень': ("👊", ['✌️']),
    'ножницы': ("✌️", ['✋']),
    'победа 1': ("🎲", [1]),
    'победа 2': ("🎲", [1]),
    'п1': ("🎲", [1]),
    'п2': ("🎲", [1]),
    'ничья': ("🎲", [1])
}

# Функции

# Калькуляция винрейта
def calculate_winrate(winning_bets, total_bets):
    if total_bets == 0:
        return 0
    winrate = (winning_bets / total_bets) * 100
    return winrate

# Генерация клавиатуры с рефералами
def generate_keyboard(page: int, refs: list, total_pages: int, per_page: int):
    start = (page - 1) * per_page
    end = start + per_page
    keyb = types.InlineKeyboardMarkup(row_width=2)
    keyb.add(types.InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data='empty_button'))
    btns = []

    for ref in refs[start:end]:
        btns.append(types.InlineKeyboardButton(text=ref[6], callback_data=f'empty_button'))

    keyb.add(*btns)

    if page > 1:
        keyb.add(types.InlineKeyboardButton(text="◀️", callback_data=f'page_{page - 1}'))
    if page < total_pages:
        keyb.add(types.InlineKeyboardButton(text="▶️", callback_data=f'page_{page + 1}'))

    keyb.add(types.InlineKeyboardButton(text="🔍 Поиск", callback_data='search_refferals'), 
           types.InlineKeyboardButton(text="◀️ Назад", callback_data='ref_panel'))

    return keyb

# Генерация текста дней
def days_text(days):
    if days % 10 == 1 and days % 100 != 11:
        return f"{days} день"
    elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
        return f"{days} дня"
    else:
        return f"{days} дней"

# Функции криптопей

# Генерация рандомного кода для перевода
def generate_random_code(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Создание счета для пополнения баланса или же казны
def create_invoice(amount):
    headers = {"Crypto-Pay-API-Token": config.CRYPTOPAY_TOKEN}
    data = {"asset": "USDT", "amount": float(amount)}
    r = requests.get("https://pay.crypt.bot/api/createInvoice", data=data, headers=headers).json()
    return r['result']['bot_invoice_url']

# Получение баланса или же казны
def get_cb_balance():
    headers = {"Crypto-Pay-API-Token": config.CRYPTOPAY_TOKEN}
    r = requests.get("https://pay.crypt.bot/api/getBalance", headers=headers).json()
    for currency_data in r['result']:
        if currency_data['currency_code'] == 'USDT':
            usdt_balance = currency_data['available']
            break
    return usdt_balance

# Трансфер или же по простому перевод
async def transfer(amount, us_id):
    bal = get_cb_balance()
    bal = float(bal)
    amount = float(amount)
    keyb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("Закрыть", callback_data='close'))
    keyb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("💼 Перейти к пользователю", url=f"tg://user?id={us_id}"))
    if bal < amount:
        try:
            await bot.send_message(us_id, f"<b>[🔔] Вам пришло системное уведомление:</b>\n\n<b><blockquote>Ваша выплата ⌊ {amount}$ ⌉ будет зачислена вручную администратором!</blockquote></b>", reply_markup=keyb)
        except:
            pass
        await bot.send_message(config.LOGS_ID, f"<b>[🔔] Мало суммы в казне для выплаты!</b>\n\n<b><blockquote>Пользователь: {us_id}\nСумма: {amount}$</blockquote></b>", reply_markup=keyb)
        return
    try:
        spend_id = generate_random_code(length=10)
        headers = {"Crypto-Pay-API-Token": config.CRYPTOPAY_TOKEN}
        data = {"asset": "USDT", "amount": float(amount), "user_id": us_id, "spend_id": spend_id}
        requests.get("https://pay.crypt.bot/api/transfer", data=data, headers=headers)
        await bot.send_message(config.LOGS_ID, f"<b>[🧾] Перевод!</b>\n\n<b>[💠] Сумма: {amount} USDT</b>\n<b>[🚀] Пользователю: {us_id}</b>", reply_markup=keyb)
    except Exception as e:
        print(e)
        return e

# Создание чека
async def create_check(amount, userid):
    bal = get_cb_balance()
    bal = float(bal)
    amount = float(amount)
    keyb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("Закрыть", callback_data='close'))
    keyb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("💼 Перейти к пользователю", url=f"tg://user?id={userid}"))
    if bal < amount:
        try:
            await bot.send_message(userid, f"<b>[🔔] Вам пришло системное уведомление:</b>\n\n<b><blockquote>Ваша выплата ⌊ {amount}$ ⌉ будет зачислена вручную администратором!</blockquote></b>", reply_markup=keyb)
        except:
            pass
        await bot.send_message(config.LOGS_ID, f"<b>[🔔] Мало суммы в казне для выплаты!</b>\n\n<b><blockquote>Пользователь: {userid}\nСумма: {amount}$</blockquote></b>", reply_markup=keyb)
        return
    headers = {"Crypto-Pay-API-Token": config.CRYPTOPAY_TOKEN}
    data = {"asset": "USDT", "amount": float(amount), "pin_to_user_id": userid}
    r = requests.get("https://pay.crypt.bot/api/createCheck", headers=headers, data=data).json()
    await bot.send_message(config.LOGS_ID, f"<b>[🧾] Создан чек!</b>\n\n<b>[💠] Сумма: {amount} USDT</b>\n<b>[🚀] Прикрепен за юзером: {userid}</b>", reply_markup=keyb)
    print(r)
    return r["result"]["bot_check_url"]

# Конвертация USD -> RUB
async def convert(amount_usd):
    headers = {"Crypto-Pay-API-Token": config.CRYPTOPAY_TOKEN}
    r = requests.get("https://pay.crypt.bot/api/getExchangeRates", headers=headers).json()
    for data in r['result']:
        if data['source'] == 'USDT' and data['target'] == 'RUB':
            rate = data['rate']
            amount_rub = float(amount_usd) * float(rate)
    return amount_rub

# Команды бота

# /start
@dp.message_handler(commands=['start'], state='*')
async def poshel_nahuy_telebot(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        msg_id = data.get('msg_id')
        await bot.delete_message(message.chat.id, msg_id)
    except:
        pass

    await state.finish()

    try:
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            msg_id = cursor.execute("SELECT msg_id FROM users WHERE us_id=?", (message.from_user.id,)).fetchone()[0]
        await bot.delete_message(message.chat.id, msg_id)
    except:
        pass

    args = message.get_args()
    if args:
        if args.startswith('ref_'):
            referrer = args.split("ref_")[1]
            if message.from_user.id == referrer:
                pass
            else:
                with sqlite3.connect("db.db") as conn:
                    cursor = conn.cursor()
                    exist = cursor.execute("SELECT * FROM users WHERE us_id=?", (message.from_user.id,)).fetchone()
                if exist:
                    pass
                else:
                    with sqlite3.connect("db.db") as conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users(us_id,username,ref) VALUES(?,?,?)", (message.from_user.id,message.from_user.mention,referrer,))
                        conn.commit()
                    await bot.send_message(referrer, f"<blockquote><b>⚡️ У вас новый реферал!\n└ {message.from_user.mention}")
                    pass

        else:
            pass
    else:
        pass

    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        exist = cursor.execute("SELECT * FROM users WHERE us_id=?", (message.from_user.id,)).fetchone()
        if not exist:
            cursor.execute("INSERT OR IGNORE INTO users(us_id,username) VALUES(?,?)", (message.from_user.id,message.from_user.mention,))
        else:
            cursor.execute("UPDATE users SET username=? WHERE us_id=?", (message.from_user.mention,message.from_user.id,))
        conn.commit()

        total_bets_summ = cursor.execute("SELECT SUM(summa) FROM bets WHERE us_id=?", (message.from_user.id,)).fetchone()[0]
        if not total_bets_summ:
            total_bets_summ = float(0.00)
            total_bets_summ = f"{total_bets_summ:.2f}"
        else:
            total_bets_summ = float(total_bets_summ)
            total_bets_summ = f"{total_bets_summ:.2f}"
        
        total_wins_summ = cursor.execute("SELECT SUM(summa) FROM bets WHERE win=1 AND us_id=?", (message.from_user.id,)).fetchone()[0]
        if not total_wins_summ:
            total_wins_summ = float(0.00)
            total_wins_summ = f"{total_wins_summ:.2f}"
        else:
            total_wins_summ = float(total_wins_summ)
            total_wins_summ = f"{total_wins_summ:.2f}"
        
        total_lose_summ = cursor.execute("SELECT SUM(summa) FROM bets WHERE lose=1 AND us_id=?", (message.from_user.id,)).fetchone()[0]
        if not total_lose_summ:
            total_lose_summ = float(0.00)
            total_lose_summ = f"{total_lose_summ:.2f}"
        else:
            total_lose_summ = float(total_lose_summ)
            total_lose_summ = f"{total_lose_summ:.2f}"

    msg = await message.answer(f"<blockquote><b>👋 Добро пожаловать в реферального бота {config.CASINO_NAME}!\n\n🎲 Статистика ваших ставок\n├ Общая сумма ставок - {total_bets_summ}$\n├ Сумма выигрышей - {total_wins_summ}$\n└ Сумма проигрышей - {total_lose_summ}$</b></blockquote>", reply_markup=kb.menu(message.from_user.id))
    await message.delete()
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET msg_id=? WHERE us_id=?", (msg.message_id,message.from_user.id,))
        conn.commit()

# Поиск реферала
@dp.message_handler(state=states.search_ref.start)
async def ref_search(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get('msg_id')
    await bot.delete_message(message.chat.id, msg_id)
    await state.finish()

    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        user = cursor.execute("SELECT * FROM users WHERE username=?", (message.text,)).fetchone()

    if not user:
        msg = await message.answer(f"<blockquote><b>🔴 {message.text} не существует!</b></blockquote>", reply_markup=kb.back("refs"))
    else:
        if user[4] != message.from_user.id:
            msg = await message.answer(f"<blockquote><b>🔴 {message.text} не ваш реферал!</b></blockquote>", reply_markup=kb.back("refs"))
        else:
            msg = await message.answer(f"<blockquote><b>🟢 {message.text} ваш реферал!</b></blockquote>", reply_markup=kb.back("refs"))
    
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET msg_id=? WHERE us_id=?", (msg.message_id,message.from_user.id,))
        conn.commit()

    await message.delete()

# Управление пользователем
@dp.message_handler(state=states.ControlUser.start)
async def control_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get('msg_id')
    await bot.delete_message(message.chat.id, msg_id)
    await state.finish()
    if message.text.isdigit():
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            user = cursor.execute("SELECT * FROM users WHERE id=?", (message.text,)).fetchone()
        if not user:
            msg = await message.answer("<blockquote><b>⚡️ Пользователь с таким ID не найден.</b></blockquote>", reply_markup=kb.back("control_user"))
        else:
            msg = await message.answer(f"<blockquote><b>⚡️ Пользователь {user[2]}</b></blockquote>", reply_markup=kb.control(user[0]))
    else:
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            user = cursor.execute("SELECT * FROM users WHERE username=?", (message.text,)).fetchone()
        if not user:
            msg = await message.answer("<blockquote><b>⚡️ Пользователь с таким username не найден.</b></blockquote>", reply_markup=kb.back("control_user"))
        else:
            msg = await message.answer(f"<blockquote><b>⚡️ Пользователь {user[2]}</b></blockquote>", reply_markup=kb.control(user[0]))
    
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET msg_id=? WHERE us_id=?", (msg.message_id,message.from_user.id,))
        conn.commit()

    await message.delete()

# Отправление сообщения пользователю
@dp.message_handler(state=states.SendMessage.start)
async def send_message_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get('msg_id')
    user_id = data.get('user_id')
    await bot.delete_message(message.chat.id, msg_id)
    await state.finish()
    await bot.send_message(user_id, f"<blockquote><b>💌 Сообщение от администратора: <code>{message.text}</code></b></blockquote>")
    msg = await message.answer("<b>⚡️ Сообщение отправлено!</b>", reply_markup=kb.back(f"control_user:{user_id}"))
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET msg_id=? WHERE us_id=?", (msg.message_id,message.from_user.id,))
        conn.commit()

    await message.delete()

# Новая максимальная ставка
@dp.message_handler(state=states.ChangeMax.start)
async def change_max(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get('msg_id')
    await bot.delete_message(message.chat.id, msg_id)
    await state.finish()
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET max_amount=?", (message.text,))
        conn.commit()
    msg = await message.answer(f"<blockquote><b>⚡️ Максимальная сумма ставки была изменена на <code>{message.text}</code> $</b></blockquote>", reply_markup=kb.back("admin"))
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET msg_id=? WHERE us_id=?", (msg.message_id,message.from_user.id,))
        conn.commit()

    await message.delete()

# Установка нового счета
@dp.message_handler(state=states.ChangeInvoice.start)
async def change_invoice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get('msg_id')
    await bot.delete_message(message.chat.id, msg_id)
    await state.finish()
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET invoice_link=?", (message.text,))
        conn.commit()
    msg = await message.answer(f"<blockquote><b>⚡️ Счет был изменен на <code>{message.text}</code></b></blockquote>", reply_markup=kb.back("admin"))
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET msg_id=? WHERE us_id=?", (msg.message_id,message.from_user.id,))
        conn.commit()

    await message.delete()

# Депозит
@dp.message_handler(state=states.Deposit.start)
async def deposit_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get('msg_id')
    await bot.delete_message(message.chat.id, msg_id)
    await state.finish()
    try:
        summa = float(message.text)
        summa_text = f"{summa:.2f}"
        invoice = create_invoice(summa)
        keyb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("⚡️ Оплатить", url=invoice), InlineKeyboardButton("◀️ Назад", callback_data='popol'))
        msg = await message.answer(f"<blockquote><b>⚡️ Пополнение казны на сумму {summa_text}$</b></blockquote>", reply_markup=keyb)
    except:
        msg = await message.answer("<blockquote><b>⚡️ Отправляйте сумму числами! Повторите попытку еще раз!", reply_markup=kb.back("admin"))
    
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET msg_id=? WHERE us_id=?", (msg.message_id,message.from_user.id,))
        conn.commit()

    await message.delete()

@dp.message_handler(state=states.Broadcast.start)
async def broadcast_handler(message: types.Message, state: FSMContext):
    if message.text == "Отмена":
        data = await state.get_data()
        msg1_id = data.get('msg1_id')
        msg2_id = data.get('msg2_id')
        await bot.delete_message(message.chat.id, msg2_id)
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            total_users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]

            total_bets = cursor.execute("SELECT COUNT(*) FROM bets").fetchone()[0]
            total_bets_summ = cursor.execute("SELECT SUM(summa) FROM bets").fetchone()[0]
            if not total_bets_summ:
                    total_bets_summ = float(0.00)
            else:
                total_bets_summ = float(total_bets_summ)
                total_bets_summ = f"{total_bets_summ:.2f}"

            total_wins = cursor.execute("SELECT COUNT(*) FROM bets WHERE win=1").fetchone()[0]
            total_wins_summ = cursor.execute("SELECT SUM(summa) FROM bets WHERE win=1").fetchone()[0]
            if not total_wins_summ:
                total_wins_summ = float(0.00)
            else:
                total_wins_summ = float(total_wins_summ)
                total_wins_summ = f"{total_wins_summ:.2f}"

            total_loses = cursor.execute("SELECT COUNT(*) FROM bets WHERE lose=1").fetchone()[0]
            total_loses_summ = cursor.execute("SELECT SUM(summa) FROM bets WHERE lose=1").fetchone()[0]
            if not total_loses_summ:
                total_loses_summ = float(0.00)
            else:
                total_loses_summ = float(total_loses_summ)
                total_loses_summ = f"{total_loses_summ:.2f}"

            msg = await bot.edit_message_text(f"<blockquote><b>⚡️ Админ-Панель\n├ Пользователей - <code>{total_users}</code> шт.\n├ Общее количество ставок - </b>~<b> <code>{total_bets}</code> шт. </b>[~ <code>{total_bets_summ}</code> <b>$</b>]\n<b>├ Выигрышей - </b>~<b> <code>{total_wins}</code> шт. </b>[~ <code>{total_wins_summ}</code> <b>$</b>]\n<b>└ Проигрышей - </b>~<b> <code>{total_loses}</code> шт. </b>[~ <code>{total_loses_summ}</code> <b>$</b>]</blockquote>", message.chat.id, msg1_id, reply_markup=kb.admin())
            with sqlite3.connect("db.db") as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET msg_id=? WHERE us_id=?", (msg.message_id,message.from_user.id,))
                conn.commit()
            await message.delete()
            return
    if message.text == "Я подтверждаю рассылку":
        data = await state.get_data()
        msg1_id = data.get('msg1_id')
        msg2_id = data.get('msg2_id')
        text = data.get('text')
        await bot.delete_message(message.chat.id, msg1_id)
        await bot.delete_message(message.chat.id, msg2_id)
        msg = await message.answer("<blockquote><b>⚡️ Идёт рассылка...</b></blockquote>")
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET msg_id=? WHERE us_id=?", (msg.message_id,message.from_user.id,))
            conn.commit()
        await message.delete()
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            users = cursor.execute("SELECT us_id FROM users").fetchall()
            failed = 0
            success = 0
            for user in users:
                try:
                    await bot.send_message(user[0], text)
                    success += 1
                except:
                    failed += 1
        msg = await msg.edit_text(f"<blockquote><b>⚡️ Рассылка завершена!\n\nОтправлено: <code>{success}</code> шт.\nНе отправлено: <code>{failed}</code> шт.</b></blockquote>", reply_markup=kb.back("admin"))
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET msg_id=? WHERE us_id=?", (msg.message_id,message.from_user.id,))
            conn.commit()
        return
    data = await state.get_data()
    msg_id = data.get('msg_id')
    await bot.delete_message(message.chat.id, msg_id)
    msg = await message.answer("""<blockquote><b>⚡️ Рассылка</b>

Вы уверены что хотите отправить данное сообщение? (Ниже пример что увидят юзеры)

<i>Для подтверждения напишите <code>Я подтверждаю рассылку</code> и для отмены напишите <code>Отмена</code></i></blockquote>""")
    msg2 = await message.answer(message.text, parse_mode="HTML")
    await state.update_data(msg1_id=msg.message_id)
    await state.update_data(msg2_id=msg2.message_id)
    await state.update_data(text=message.text)
    await message.delete()

# Колбэки
@dp.callback_query_handler(lambda call: True, state='*')
async def calls(call: types.CallbackQuery, state: FSMContext):
    await state.finish()

    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        exist = cursor.execute("SELECT * FROM users WHERE us_id=?", (call.from_user.id,)).fetchone()
        if not exist:
            cursor.execute("INSERT OR IGNORE INTO users(us_id,username) VALUES(?,?)", (call.from_user.id,call.from_user.mention,))
        else:
            cursor.execute("UPDATE users SET username=? WHERE us_id=?", (call.from_user.mention,call.from_user.id,))
        conn.commit()
    
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET msg_id=? WHERE us_id=?", (call.message.message_id,call.from_user.id,))
        conn.commit()

    if call.data == 'profile':
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            winning_bets = cursor.execute("SELECT COUNT(*) FROM bets WHERE win=1 AND us_id=?", (call.from_user.id,)).fetchone()[0]
            total_bets = cursor.execute("SELECT COUNT(*) FROM bets WHERE us_id=?", (call.from_user.id,)).fetchone()[0]
            total_bets_summ = cursor.execute("SELECT SUM(summa) FROM bets WHERE us_id=?", (call.from_user.id,)).fetchone()[0]
            if not total_bets_summ:
                total_bets_summ = float(0.00)
            else:
                total_bets_summ = float(total_bets_summ)
                total_bets_summ = f"{total_bets_summ:.2f}"
            join_date_str = cursor.execute("SELECT join_date FROM users WHERE us_id=?", (call.from_user.id,)).fetchone()[0]

        winrate = calculate_winrate(winning_bets, total_bets)
        winrate = f"{winrate:.2f}"
        join_date = datetime.strptime(join_date_str, "%Y-%m-%d %H:%M:%S")
        current_date = datetime.now()
        difference = current_date - join_date
        days_joined = difference.days
        days_joined_text = days_text(days_joined)
        formatted_date_str = join_date.strftime("%d.%m.%Y")

        await call.answer()
        await call.message.edit_text(f"""<blockquote><b>⚡️ Профиль {call.from_user.first_name}\n\nℹ️ Информация\n├ WinRate - <code>{winrate}%</code>\n├ Ставки за все время - <code>{total_bets_summ}$</code> за <code>{total_bets}</code> игр\n└ Дата регистрации - <code>{formatted_date_str}</code> </b>(<code>{days_joined_text}</code>)</blockquote>""", reply_markup=kb.profile())
    elif call.data == 'menu':
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()

            total_bets_summ = cursor.execute("SELECT SUM(summa) FROM bets WHERE us_id=?", (call.from_user.id,)).fetchone()[0]
            if not total_bets_summ:
                total_bets_summ = float(0.00)
                total_bets_summ = f"{total_bets_summ:.2f}"
            else:
                total_bets_summ = float(total_bets_summ)
                total_bets_summ = f"{total_bets_summ:.2f}"
            
            total_wins_summ = cursor.execute("SELECT SUM(summa) FROM bets WHERE win=1 AND us_id=?", (call.from_user.id,)).fetchone()[0]
            if not total_wins_summ:
                total_wins_summ = float(0.00)
                total_wins_summ = f"{total_wins_summ:.2f}"
            else:
                total_wins_summ = float(total_wins_summ)
                total_wins_summ = f"{total_wins_summ:.2f}"
            
            total_lose_summ = cursor.execute("SELECT SUM(summa) FROM bets WHERE lose=1 AND us_id=?", (call.from_user.id,)).fetchone()[0]
            if not total_lose_summ:
                total_lose_summ = float(0.00)
                total_lose_summ = f"{total_lose_summ:.2f}"
            else:
                total_lose_summ = float(total_lose_summ)
                total_lose_summ = f"{total_lose_summ:.2f}"

        await call.answer()
        await call.message.edit_text(f"<blockquote><b>👋 Добро пожаловать в реферального бота {config.CASINO_NAME}!\n\n🎲 Статистика ваших ставок\n├ Общая сумма ставок - {total_bets_summ}$\n├ Сумма выигрышей - {total_wins_summ}$\n└ Сумма проигрышей - {total_lose_summ}$</b></blockquote>", reply_markup=kb.menu(call.from_user.id))
    elif call.data == 'stats':
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()

            total_games = cursor.execute("SELECT COUNT(*) FROM bets").fetchone()[0]
            total_payouts = cursor.execute("SELECT SUM(summa) FROM bets WHERE win=1").fetchone()[0]

            if not total_payouts:
                total_payouts = round(0.00)
            else:
                total_payouts = round(total_payouts)

            formatted_wins = f"{total_payouts:,}".replace(",", " ")
            total_rub = await convert(total_payouts)
            total_rub = round(total_rub)
            formatted_rub = f"{total_rub:,}".replace(",", " ")
        
        await call.answer()
        await call.message.edit_text(f"<blockquote><b>⚡️ Статистика о нашем проекте\n├ Общее количество игр - <code>{total_games}</code> шт.\n├ \n├ Сумма общих выплат:\n├ <code>{formatted_wins}$</code>\n└ <code>{formatted_rub}₽</code></b></blockquote>", reply_markup=kb.back("menu"))
    elif call.data == 'ref_panel':
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            total_refs = cursor.execute("SELECT COUNT(*) FROM users WHERE ref=?", (call.from_user.id,)).fetchone()[0]
            ref_balance = cursor.execute("SELECT ref_balance FROM users WHERE us_id=?", (call.from_user.id,)).fetchone()[0]
            ref_balance = float(ref_balance)
            ref_balance = f"{ref_balance:.2f}"
        await call.answer()
        bot_username = await bot.get_me()
        await call.message.edit_text(f"<blockquote><b>⚡️ Реферальная панель\n├ Вы будете получать <code>10%</code> от проигрыша вашего реферала\n├ Вывод доступен от <code>0.2$</code>\n├ \n├ Количество рефералов - <code>{total_refs}</code> шт.\n├ Ваш реферальный баланс - <code>{ref_balance}$</code>\n└ Реф. Ссылка - <code>https://t.me/{bot_username.username}?start=ref_{call.from_user.id}</code></b></blockquote>", reply_markup=kb.ref())
    elif call.data == 'refs':
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            refs = cursor.execute("SELECT * FROM users WHERE ref=?", (call.from_user.id,)).fetchall()

        per_page = 10
        total_pages = (len(refs) - 1) // per_page + 1
        btns = []

        def generate_keyboard1(page: int):
            start = (page - 1) * per_page
            end = start + per_page
            keyb = types.InlineKeyboardMarkup(row_width=2)
            keyb.add(types.InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data='empty_button'))

            for ref in refs[start:end]:
                btns.append(types.InlineKeyboardButton(text=ref[6], callback_data=f'empty_button'))

            keyb.add(*btns)

            if page > 1:
                keyb.add(types.InlineKeyboardButton(text="◀️", callback_data=f'page_{page - 1}'))
            if page < total_pages:
                keyb.add(types.InlineKeyboardButton(text="▶️", callback_data=f'page_{page + 1}'))

            keyb.add(types.InlineKeyboardButton(text="🔍 Поиск", callback_data='search_refferals'), 
                   types.InlineKeyboardButton(text="◀️ Назад", callback_data='ref_panel'))

            return keyb

        page = 1
        keyb = generate_keyboard1(page)

        await call.answer()
        await call.message.edit_text(f"<blockquote><b>📄 Вы открыли страницу {page}/{total_pages}:</b></blockquote>", reply_markup=keyb)
    elif call.data.startswith('page_'):
        page = int(call.data.split('_')[1])
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            refs = cursor.execute("SELECT * FROM users WHERE ref=?", (call.from_user.id,)).fetchall()
        per_page = 10
        total_pages = (len(refs) - 1) // per_page + 1

        keyb = generate_keyboard(page, refs, total_pages, per_page)
        await call.message.edit_text(f"<blockquote><b>📄 Вы открыли страницу {page}/{total_pages}:</b></blockquote>", reply_markup=keyb)
    elif call.data == 'search_refferals':
        await state.finish()
        await call.message.edit_text("<blockquote><b>⚡️ Введите @username реферала:</b></blockquote>", reply_markup=kb.back("refs"))
        await states.search_ref.start.set()
        await state.update_data(msg_id=call.message.message_id)
    elif call.data == 'cashback':
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            cashback = cursor.execute("SELECT cashback FROM users WHERE us_id=?", (call.from_user.id,)).fetchone()[0]
        await call.answer()
        await call.message.edit_text(f"<blockquote><b>⚡️ Панель кэшбек системы\n├ В случае проигрыша вы получаете <code>7.5%</code> от суммы ставки\n├ Вывод доступен от <code>0.2$</code>\n└ Кэшбек-счет - <code>{cashback:.2f}$</code></b></blockquote>", reply_markup=kb.cashback())
    elif call.data == 'admin':
        if call.from_user.id in config.ADMINS:
            with sqlite3.connect("db.db") as conn:
                cursor = conn.cursor()
                total_users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]

                total_bets = cursor.execute("SELECT COUNT(*) FROM bets").fetchone()[0]
                total_bets_summ = cursor.execute("SELECT SUM(summa) FROM bets").fetchone()[0]
                if not total_bets_summ:
                    total_bets_summ = float(0.00)
                else:
                    total_bets_summ = float(total_bets_summ)
                    total_bets_summ = f"{total_bets_summ:.2f}"

                total_wins = cursor.execute("SELECT COUNT(*) FROM bets WHERE win=1").fetchone()[0]
                total_wins_summ = cursor.execute("SELECT SUM(summa) FROM bets WHERE win=1").fetchone()[0]
                if not total_wins_summ:
                    total_wins_summ = float(0.00)
                else:
                    total_wins_summ = float(total_wins_summ)
                    total_wins_summ = f"{total_wins_summ:.2f}"

                total_loses = cursor.execute("SELECT COUNT(*) FROM bets WHERE lose=1").fetchone()[0]
                total_loses_summ = cursor.execute("SELECT SUM(summa) FROM bets WHERE lose=1").fetchone()[0]
                if not total_loses_summ:
                    total_loses_summ = float(0.00)
                else:
                    total_loses_summ = float(total_loses_summ)
                    total_loses_summ = f"{total_loses_summ:.2f}"

                await call.answer()
                await call.message.edit_text(f"<blockquote><b>⚡️ Админ-Панель\n├ Пользователей - <code>{total_users}</code> шт.\n├ Общее количество ставок - </b>~<b> <code>{total_bets}</code> шт. </b>[~ <code>{total_bets_summ}</code> <b>$</b>]\n<b>├ Выигрышей - </b>~<b> <code>{total_wins}</code> шт. </b>[~ <code>{total_wins_summ}</code> <b>$</b>]\n<b>└ Проигрышей - </b>~<b> <code>{total_loses}</code> шт. </b>[~ <code>{total_loses_summ}</code> <b>$</b>]</blockquote>", reply_markup=kb.admin())
    elif call.data == 'control_user':
        if call.from_user.id in config.ADMINS:
            await call.answer()
            await call.message.edit_text("<blockquote><b>⚡️ Отправьте @username или ID пользователя:</b></blockquote>", reply_markup=kb.back("admin"))
            await states.ControlUser.start.set()
            await state.update_data(msg_id=call.message.message_id)
    elif call.data.startswith("control_user:"):
        if call.from_user.id in config.ADMINS:
            userid = call.data.split(":")[1]
            with sqlite3.connect("db.db") as conn:
                cursor = conn.cursor()
                user = cursor.execute("SELECT * FROM users WHERE us_id=?", (userid,)).fetchone()
            await call.answer()
            await call.message.edit_text(f"<blockquote><b>⚡️ Пользователь {user[2]}</b></blockquote>", reply_markup=kb.control(user[0]))
    elif call.data.startswith("empty_ref:"):
        if call.from_user.id in config.ADMINS:
            userid = call.data.split(":")[1]
            with sqlite3.connect("db.db") as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET ref_balance=0 WHERE us_id=?", (userid,))
                conn.commit()
            await call.answer("Анулирован!", show_alert=True)
    elif call.data.startswith("empty_cashback:"):
        if call.from_user.id in config.ADMINS:
            userid = call.data.split(":")[1]
            with sqlite3.connect("db.db") as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET cashback=0 WHERE us_id=?", (userid,))
                conn.commit()
            await call.answer("Анулирован!", show_alert=True)
    elif call.data.startswith("send_message:"):
        if call.from_user.id in config.ADMINS:
            userid = call.data.split(":")[1]
            await call.answer()
            await call.message.edit_text("<blockquote><b>⚡️ Введите текст который хотите отправить пользователю:</b></blockquote>", reply_markup=kb.back(f"control_user:{userid}"))
            await states.SendMessage.start.set()
            await state.update_data(user_id=userid)
            await state.update_data(msg_id=call.message.message_id)
    elif call.data == 'change_max':
        if call.from_user.id in config.ADMINS:
            await call.answer()
            await call.message.edit_text("<blockquote><b>⚡️ Введите новую сумму максимальной ставки:</b></blockquote>", reply_markup=kb.back("admin"))
            await states.ChangeMax.start.set()
            await state.update_data(msg_id=call.message.message_id)
    elif call.data == 'change_invoice':
        if call.from_user.id in config.ADMINS:
            await call.answer()
            await call.message.edit_text("<blockquote><b>⚡️ Введите новую ссылку на счет:</b></blockquote>", reply_markup=kb.back("admin"))
            await states.ChangeInvoice.start.set()
            await state.update_data(msg_id=call.message.message_id)
    elif call.data == 'popol':
        if call.from_user.id in config.ADMINS:
            await call.answer()
            balance = get_cb_balance()
            balance = float(balance)
            balance2 = max(balance - 0.01, 0)
            await call.message.edit_text(f"<blockquote><b>⚡️ Введите сумму на которую хотите пополнить казну:</b>\n\n<b>⚡️ Текущий баланс: <code>{balance}</code> USDT </b>[~ <code>{balance2}</code> <b>$</b>]</blockquote>", reply_markup=kb.back("admin"))
            await states.Deposit.start.set()
            await state.update_data(msg_id=call.message.message_id)
    elif call.data == 'broadcast':
        if call.from_user.id in config.ADMINS:
            await call.answer()
            await call.message.edit_text("<blockquote><b>⚡️ Введите текст для рассылки</b></blockquote>", reply_markup=kb.back("admin"))
            await states.Broadcast.start.set()
            await state.update_data(msg_id=call.message.message_id)
    elif call.data == 'links':
        await call.answer("Временно не работает.", show_alert=True)
    else:
        await call.answer()

# Неизвестная команда
@dp.message_handler()
async def unknown_command(message: types.Message):
    await message.delete()

# Сам код твоего бота измененный мною
def parse_message(message):
    message = re.sub(r"\[🪙\]\(tg://emoji\?id=\d+\)", "", message)
    start_index = message.find("tg://user?id=") + len("tg://user?id=")
    end_index = message.find(")", start_index)
    user_id = message[start_index:end_index]
    amount_start_index = message.find("($") + 2
    amount_end_index = message.find(")", amount_start_index)
    amount = float(message[amount_start_index:amount_end_index].strip().replace("\\", "").replace("*", ""))
    username_start_index = message.find("[*")
    username_end_index = message.find("*]", username_start_index)
    username = message[username_start_index + 2:username_end_index].replace("\\", "")
    username = re.sub(r'@[\w]+', f'{config.CASINO_NAME}', username) if '@' in username else username
    comment = message.split('\n')[-1]
    comment = str(comment.lower()).replace("💬 ", "")

    match = {
        "id": user_id,
        "name": username,
        "usd_amount": amount,
        "comment": comment
    }

    return match if match else None

def create_keyboard(check=None, summa=None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if check == None and summa == None:
        bet_button = InlineKeyboardButton("Сделать ставку", url=config.BET_URL)
        keyboard.add(bet_button)
    else:
        claim_check = InlineKeyboardButton(f"🎁 Забрать {summa}$", url=check)
        bet_button = InlineKeyboardButton("Сделать ставку", url=config.BET_URL)
        keyboard.add(claim_check, bet_button)
    return keyboard

async def send_result_message(result, parsed_data, dice_result, coefficient, us_id, msg_id):
    emoji, winning_values = DICE_CONFIG[parsed_data['comment']]
    bot_username = await bot.get_me()
    bot_username = bot_username.username

    if 'камень' in parsed_data['comment'] or 'ножницы' in parsed_data['comment'] or 'бумага' in parsed_data['comment']:
        choose = ['✋', '👊', '✌️']
        choice = random.choice(choose)
        await asyncio.sleep(1)
        msg_dice = await bot.send_message(config.CHANNEL_ID, text=choice, reply_to_message_id=msg_id)
        dice_value = msg_dice.text
        result = dice_value in winning_values
        if result:
            result = True
        elif not result:
            result = False
        else:
            result = False
    
    if 'победа 1' in parsed_data['comment'] or 'п1' in parsed_data['comment'] or 'победа 2' in parsed_data['comment'] or 'п2' in parsed_data['comment'] or 'ничья' in parsed_data['comment']:
        dice1 = dice_result
        dice2 = await bot.send_dice(config.CHANNEL_ID, emoji=emoji, reply_to_message_id=msg_id)
        dice2 = dice2.dice.value

        if dice1 > dice2:
            if 'победа 1' in parsed_data['comment'] or 'п1' in parsed_data['comment']:
                result = True
            else:
                result = False
        elif dice1 < dice2:
            if 'победа 2' in parsed_data['comment'] or 'п2' in parsed_data['comment']:
                result = True
            else:
                result = False
        elif dice1 == dice2:
            if 'ничья' in parsed_data['comment']:
                result = True
            else:
                result = False

    if result:
        usd_amount = parsed_data['usd_amount']
        usd_amount = float(usd_amount)
        minus_cashback = usd_amount * (7.5 / 100)
        print(minus_cashback)
        print(usd_amount)

        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO bets(us_id, summa, win) VALUES(?, ?, 1)", (parsed_data['id'], usd_amount,))
            cursor.execute("UPDATE users SET cashback=cashback-? WHERE us_id=?", (minus_cashback, parsed_data['id'],))
            conn.commit()
            user = cursor.execute("SELECT cashback FROM users WHERE us_id=?", (parsed_data['id'],)).fetchone()[0]
            print(user)
            if float(user) < float(0):
                cursor.execute("UPDATE users SET cashback=0.0 WHERE us_id=?", (parsed_data['id'],))
                conn.commit()

        if 'плинко' in parsed_data['comment']:
            if dice_result == 4:
                winning_amount_usd = float(parsed_data['usd_amount'] * 1.8)
            elif dice_result == 5:
                winning_amount_usd = float(parsed_data['usd_amount'] * 2)
            elif dice_result == 6:
                winning_amount_usd = float(parsed_data['usd_amount'] * 2.5)
        else:
            winning_amount_usd = float(parsed_data['usd_amount']) * coefficient

        cb_balance = get_cb_balance()
        cb_balance = float(cb_balance)
        if cb_balance < winning_amount_usd:
            keyb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("💼 Перейти к пользователю", url=f"tg://user?id={us_id}"))
            await bot.send_message(config.LOGS_ID, f"<b>[🔔] Мало суммы в казне для выплаты!</b>\n\n<b><blockquote>Пользователь: {us_id}\nСумма: {winning_amount_usd}$</blockquote></b>", reply_markup=keyb)
            keyboard = create_keyboard()
            result_message = (
                f"<b>🎉 Поздравляем, вы выиграли {winning_amount_usd:.2f} USD!</b>\n\n"
                f"<blockquote><b>🚀 Ваш выигрыш будет зачислен <u>вручную</u> <u>администрацией</u>.\n🔥 Удачи в следующих ставках!</b></blockquote>\n\n"
                f"<a href='{config.RULES_LINK}'>Правила</a> | <a href='{config.NEWS_LINK}'>Новостной</a> | <a href='https://t.me/{bot_username}'>Реферальный бот</a> | <a href='{config.PEREHOD_LINK}'>Ссылка для друга</a>"
            )
        else:
            if winning_amount_usd >= 1.12:
                transfer(winning_amount_usd, us_id)
                keyboard = create_keyboard()
                result_message = (
                    f"<b>🎉 Поздравляем, вы выиграли {winning_amount_usd:.2f} USD!</b>\n\n"
                    f"<blockquote><b>🚀 Ваш выигрыш успешно <u>зачислен</u> на <u>ваш</u> <u>CryptoBot</u> <u>кошелёк</u>.\n🔥 Желаю удачи в следующих ставках!</b></blockquote>\n\n"
                    f"<a href='{config.RULES_LINK}'>Правила</a> | <a href='{config.NEWS_LINK}'>Новостной</a> | <a href='https://t.me/{bot_username}'>Реферальный бот</a> | <a href='{config.PEREHOD_LINK}'>Ссылка для друга</a>"
                )
            else:
                check = create_check(winning_amount_usd, us_id)
                keyboard = create_keyboard(check, winning_amount_usd)
                result_message = (
                    f"<b>🎉 Поздравляем, вы выиграли {winning_amount_usd:.2f} USD!</b>\n\n"
                    f"""<blockquote><b>🚀 <u>Заберите</u> <u>ваш</u> <u>CryptoBot</u> <u>чек</u> ниже\n🔥 Желаю удачи в следующих ставках!</b></blockquote>\n\n"""
                    f"<a href='{config.RULES_LINK}'>Правила</a> | <a href='{config.NEWS_LINK}'>Новостной</a> | <a href='https://t.me/{bot_username}'>Реферальный бот</a> | <a href='{config.PEREHOD_LINK}'>Ссылка для друга</a>"
                )
    else:
        usd_amount = parsed_data['usd_amount']
        usd_amount = float(usd_amount)
        add_cashback = usd_amount * (7.5 / 100)
        add_ref = usd_amount * (10 / 100)

        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO bets(us_id,summa,lose) VALUES(?,?,1)", (parsed_data['id'],usd_amount,))
            cursor.execute("UPDATE users SET cashback=cashback+? WHERE us_id=?", (add_cashback,parsed_data['id'],))
            conn.commit()
            ref = cursor.execute("SELECT ref FROM users WHERE us_id=?", (parsed_data['id'],)).fetchone()[0]
            if not ref:
                pass
            else:
                cursor.execute("UPDATE users SET ref_balance=ref_balance+? WHERE us_id=?", (add_ref,ref,))
                conn.commit()
                await bot.send_message(ref, f"<blockquote><b>⚡️ Выплата с реферала!</b>\n\n<b>⚡️ +{add_ref}$ на реферальный баланс!</b></blockquote>")

        keyboard = create_keyboard()
        result_message = (
            f"<b>[❌] Проигрыш</b>\n\n"
            "<blockquote><b>Не удачная ставка, сделай ставку ещё раз чтобы испытать удачу сполна!\n\n"
            "😞 Желаю удачи в следующий раз!</b></blockquote>\n\n"
            f"<b>- Вам начислен кэшбек! +{add_cashback:.2f}$ на ваш кэшбек-счет</b>\n\n"
            f"<a href='{config.RULES_LINK}'>Правила</a> | <a href='{config.NEWS_LINK}'>Новостной</a> | <a href='https://t.me/{bot_username}'>Реферальный бот</a> | <a href='{config.PEREHOD_LINK}'>Ссылка для друга</a>"
        )

    return result_message, keyboard

async def handle_bet(parsed_data, bet_type, us_id, msg_id, oplata_id):
    try:
        emoji, winning_values = DICE_CONFIG[bet_type]
        if 'камень' in parsed_data['comment'] or 'ножницы' in parsed_data['comment'] or 'бумага' in parsed_data['comment']:
            dice_message = await bot.send_message(config.CHANNEL_ID, text=emoji, reply_to_message_id=msg_id)
            dice_result = dice_message.text
            result = None
            result_message, keyboard = await send_result_message(result, parsed_data, dice_result, COEFFICIENTS[bet_type], us_id, msg_id)
        elif 'победа 1' in parsed_data['comment'] or 'п1' in parsed_data['comment'] or 'победа 2' in parsed_data['comment'] or 'п2' in parsed_data['comment'] or 'ничья' in parsed_data['comment']:
            dice1 = await bot.send_dice(config.CHANNEL_ID, emoji=emoji, reply_to_message_id=msg_id)
            dice_result = dice1.dice.value
            result = None
            result_message, keyboard = await send_result_message(result, parsed_data, dice_result, COEFFICIENTS[bet_type], us_id, msg_id)
        else:
            dice_message = await bot.send_dice(config.CHANNEL_ID, emoji=emoji, reply_to_message_id=msg_id) if emoji else await bot.send_dice(config.CHANNEL_ID, reply_to_message_id=msg_id)
            dice_result = dice_message.dice.value
            result = dice_result in winning_values
            result_message, keyboard = await send_result_message(result, parsed_data, dice_result, COEFFICIENTS[bet_type], us_id, msg_id)
        await asyncio.sleep(4)
        if 'вы выиграли' in result_message:
            keyb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("💼 Перейти к пользователю", url=f"tg://user?id={us_id}"))
            await bot.send_message(config.LOGS_ID, """<blockquote><b>🎲 Исход ставки: <span class="tg-spoiler">🔥 Победа!</span></b></blockquote>""", reply_markup=keyb, reply_to_message_id=oplata_id)
            await bot.send_photo(config.CHANNEL_ID, open(config.WIN_IMAGE, 'rb'), result_message, reply_markup=keyboard, reply_to_message_id=msg_id)
        else:
            keyb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("💼 Перейти к пользователю", url=f"tg://user?id={us_id}"))
            await bot.send_message(config.LOGS_ID, """<blockquote><b>🎲 Исход ставки: <span class="tg-spoiler">❌ Проигрыш!</span></b></blockquote>""", reply_markup=keyb, reply_to_message_id=oplata_id)
            await bot.send_photo(config.CHANNEL_ID, open(config.LOSE_IMAGE, 'rb'), result_message, reply_markup=keyboard, reply_to_message_id=msg_id)
    except Exception as e:
        await bot.send_message(config.LOGS_ID, f"<blockquote><b>❌ Ошибка при обработке ставки: <code>{str(e)}</code></b></blockquote>")

queue_file = 'bet_queue.txt'
processing_lock = asyncio.Lock()

async def add_bet_to_queue(user_id, username, amount, comment, msg_id):
    with open(queue_file, 'a', encoding='utf-8') as file:
        file.write(f"{user_id}‎ {username}‎ {amount}‎ {comment}‎ {msg_id}\n")

@dp.channel_post_handler()
async def check_messages(message: types.Message):
    try:
        if message.chat.id == config.LOGS_ID:
            if 'отправил(а)' in message.text:
                try:
                    async with processing_lock:
                        parsed_data = parse_message(message.md_text)

                        with sqlite3.connect("db.db") as conn:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO deposits(us_id,summa) VALUES(?,?)", (parsed_data['id'],parsed_data['usd_amount'],))
                            conn.commit()

                        await add_bet_to_queue(parsed_data['id'], parsed_data['name'], parsed_data['usd_amount'], parsed_data['comment'], message.message_id)
                        await asyncio.sleep(1)

                        if os.path.exists(queue_file):
                            with open(queue_file, 'r', encoding='utf-8') as file:
                                lines = file.readlines()

                            processed_lines = []
                            for line in lines:
                                parts = line.strip().split('‎ ')
                                if len(parts) != 5:
                                    continue

                                user_id, username, amount, comment_lower, msg_id = parts
                                amount = float(amount)
                                amount = f"{amount:.2f}"
                                amount = float(amount)
                                if not comment_lower or not comment_lower.strip():
                                    error_message = (
                                        f"<b>[❌] Ошибка!\n\n<blockquote>{username}, вы забыли дописать комментарий к ставке.</blockquote></b>"
                                    )
                                    await bot.send_message(config.CHANNEL_ID, error_message)
                                    return

                                bet_msg = await bet_sender.send_bet(username, amount, comment_lower)

                                for bet_type in DICE_CONFIG.keys():
                                    if bet_type in message.text.lower():
                                        await handle_bet(parsed_data, bet_type, user_id, bet_msg, msg_id)
                                        break
                                processed_lines.append(line)
                                await asyncio.sleep(1)
                            with open(queue_file, 'w', encoding='utf-8') as file:
                                for line in lines:
                                    if line not in processed_lines:
                                        file.write(line)
                                return
                except Exception as e:
                    await bot.send_message(config.LOGS_ID, f"<blockquote><b>❌ Ошибка при обработке сообщения: <code>{str(e)}</code></b></blockquote>")
    except Exception as e:
        await bot.send_message(config.LOGS_ID, f"<blockquote><b>❌ Ошибка при обработке сообщения: <code>{str(e)}</code></b></blockquote>")

if __name__ == '__main__':
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS users(
        us_id INT UNIQUE,
        join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        username TEXT,
        ref INT,
        ref_balance REAL DEFAULT 0.0,
        cashback REAL DEFAULT 0.0,
        ref_total REAL DEFAULT 0.0,
        msg_id INT
);""")
        conn.execute("""CREATE TABLE IF NOT EXISTS deposits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        summa INT,
        us_id INT
);""")
        conn.execute("""CREATE TABLE IF NOT EXISTS bets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        summa REAL,
        win INT DEFAULT 0,
        lose INT DEFAULT 0,
        us_id INT
);""")
        conn.execute("""CREATE TABLE IF NOT EXISTS settings(
        invoice_link TEXT PRIMARY KEY,
        max_amount DEFAULT 25,
        podkrut INT DEFAULT 0
);""")
        conn.commit()
        conn.execute("INSERT OR IGNORE INTO settings(invoice_link) VALUES('https://google.com')")
        conn.commit()
    executor.start_polling(dp, skip_updates=True)