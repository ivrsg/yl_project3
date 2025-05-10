import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from configs import TOKEN
import sqlite3

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)


async def start(update, context):
    con = sqlite3.connect('finance.db')
    cur = con.cursor()
    name = update.message.from_user.username
    result = cur.execute("""SELECT id FROM users
                WHERE username=?""", (name,)).fetchall()
    if not result:
        # добавляет к бд если новый пользователь
        cur.execute("""INSERT INTO users(username) VALUES(?)""", (name,))
        con.commit()
    con.close()
    reply_keyboard = [['/add'], ['/lim']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text('Здравствуйте...', reply_markup=markup)  # дописать красиво


async def add(update, context):
    reply_keyboard = [['Добавить единоразовую трату'], ['Добавить регулярную трату']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text('Вы хотите добавить регулярную трату или единоразовую?', reply_markup=markup)
    return 1


async def add1(update, context):
    reply_keyboard = [['Транспорт', 'Здоровье'], ['Кафе/Продукты', 'Развлечения']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    if update.message.text == 'Добавить единоразовую трату':
        await update.message.reply_text('Выберите к какой категории она относится.', reply_markup=markup)
        return 2
    elif update.message.text == 'Добавить регулярную трату':
        await update.message.reply_text('Выберите к какой категории она относится.', reply_markup=markup)
        return 3
    else:
        await update.message.reply_text('Вы хотите добавить регулярную трату или единоразовую?')
        return 1


async def add_one(update, context):
    context.user_data['category'] = update.message.text
    await update.message.reply_text('Какую сумму вы потратили?\n'
                                    'Напишите только сумму в рублях в формате "рубли.копейки".',
                                    reply_markup=ReplyKeyboardRemove())
    return 4


async def add_one_sum(update, context):
    try:
        con = sqlite3.connect('finance.db')
        cur = con.cursor()
        name = update.message.from_user.username
        usid = cur.execute("""SELECT id FROM users
                        WHERE username=?""", (name,)).fetchall()[0][0]
        cteg = cur.execute("""SELECT id, sum, lim FROM expenses
                        WHERE users_id=? and category=?""", (usid, context.user_data['category'])).fetchall()
        if not cteg:
            cur.execute("""INSERT INTO expenses(users_id, category, sum, regular) VALUES(?, ?, ?, False)""",
                        (usid, context.user_data['category'], float(update.message.text)))
            reply_keyboard = [['/add'], ['/lim']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            await update.message.reply_text('Готово!\n'
                                            'Если хотите добавить лимит на категорию, напишите /lim.',
                                            reply_markup=markup)
        else:
            if cteg[0][2] and cteg[0][1] + float(update.message.text) > cteg[0][2]:
                reply_keyboard = [['/add'], ['/lim']]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
                await update.message.reply_text(
                    f'Мы не можем добавить расход к общей сумме, так как он превышает лимит на'
                    f' {cteg[0][1] + float(update.message.text) - cteg[0][2]} рублей.\n'
                    f'Для начала поменяйте его командой /lim.',
                    reply_markup=markup)
            else:
                cur.execute("""UPDATE expenses
                SET sum = ?
                WHERE id = ?""", (cteg[0][1] + float(update.message.text), cteg[0][0]))
                reply_keyboard = [['/add'], ['/lim']]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
                await update.message.reply_text('Готово!',
                                                reply_markup=markup)
        con.commit()
        con.close()
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text('Какую сумму вы потратили?\n'
                                        'Напишите только сумму в рублях в формате "рубли.копейки".')
        return 4


async def add_regular(update, context):
    ...  # добавить регулярные платежи


async def lim(update, context):
    reply_keyboard = [['Транспорт', 'Здоровье'], ['Продукты питания', 'Рестораны и кафе']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text('На какую категорию вы хотите установить лимит?',
                                    reply_markup=markup)
    return 1


async def limcategor(update, context):
    context.user_data['category'] = update.message.text
    await update.message.reply_text('Какой лимит вы хотите установить?\n'
                                    'Напишите только сумму в рублях в формате "рубли.копейки".',
                                    reply_markup=ReplyKeyboardRemove())
    return 2


async def limsum(update, context):
    try:
        con = sqlite3.connect('finance.db')
        cur = con.cursor()
        name = update.message.from_user.username
        usid = cur.execute("""SELECT id FROM users
                        WHERE username=?""", (name,)).fetchall()[0][0]
        cteg = cur.execute("""SELECT id FROM expenses
                        WHERE users_id=? and category=?""", (usid, context.user_data['category'])).fetchall()
        if not cteg:
            cur.execute("""INSERT INTO expenses(users_id, category, lim, regular) VALUES(?, ?, ?, False)""",
                        (usid, context.user_data['category'], float(update.message.text)))
        else:
            cur.execute("""UPDATE expenses
            SET lim = ?
            WHERE id = ?""", (float(update.message.text), cteg[0][0]))
        reply_keyboard = [['/add'], ['/lim']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text('Готово!',
                                        reply_markup=markup)
        con.commit()
        con.close()
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text('Какой лимит вы хотите установить?\n'
                                        'Напишите только сумму в рублях в формате "рубли.копейки".')
        return 2


async def stop(update, context):
    reply_keyboard = [['/add'], ['/lim']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text("Ну, ладно", reply_markup=markup)
    return ConversationHandler.END


def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add1)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_one)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_regular)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_one_sum)]},
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(conv_handler)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('lim', lim)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, limcategor)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, limsum)]},
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
