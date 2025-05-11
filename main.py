import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from configs import TOKEN
import sqlite3

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='logging.log', level=logging.DEBUG)

logger = logging.getLogger(__name__)


def nick(name):
    con = sqlite3.connect('finance.db')
    cur = con.cursor()
    nickname = cur.execute("""SELECT nickname FROM users
                        WHERE username=?""", (name,)).fetchone()[0]
    if not nickname:
        nickname = name
    con.close()
    return nickname


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

    reply_keyboard = [['/add'], ['/lim']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    nickname = cur.execute("""SELECT nickname FROM users
                    WHERE username=?""", (name,)).fetchone()[0]
    if nickname:
        context.user_data['nickname'] = nickname
        name = nickname
    con.close()
    await update.message.reply_text(f'Здравствуйте...{name}))', reply_markup=markup)


async def help(update, context):
    name = update.message.from_user.username
    await update.message.reply_text(f'Здравствуйте...{nick(name)}))\n'
                                    f'\n'
                                    f'Вот список команд для настройки бота: \n'
                                    f'\n'
                                    f'/rename - установите, как к вам будет обращаться бот.\n'
                                    f'/stop - возвращение в главное меню.\n'
                                    f'/clear - очистить все данные пользователя.\n'
                                    f'/add_category - добавить собственную категорию трат')


async def rename(update, context):
    con = sqlite3.connect('finance.db')
    cur = con.cursor()
    name = update.message.from_user.username
    result = cur.execute("""SELECT id FROM users
                    WHERE username=?""", (name,)).fetchall()
    if not result:
        cur.execute("""INSERT INTO users(username) VALUES(?)""", (name,))
        con.commit()
    con.close()
    await update.message.reply_text(f'Как к вам обращаться...{name}? ))')
    return 1


async def set_nickname(update, context):
    context.user_data['nickname'] = update.message.text
    nickname = context.user_data['nickname']
    con = sqlite3.connect('finance.db')
    cur = con.cursor()
    name = update.message.from_user.username
    cur.execute("UPDATE users SET nickname = ? WHERE username = ?", (nickname, name))
    con.commit()
    con.close()
    await update.message.reply_text(f'Теперь вы для меня {context.user_data["nickname"]}... ))')


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
    if update.message.text in ['Транспорт', 'Здоровье', 'Кафе/Продукты', 'Развлечения']:
        context.user_data['category'] = update.message.text
        await update.message.reply_text('Какую сумму вы потратили?\n'
                                        'Напишите только сумму в рублях в формате "рубли.копейки".',
                                        reply_markup=ReplyKeyboardRemove())
        return 4
    await update.message.reply_text('Выберите к какой категории она относится.')
    return 2


async def add_one_sum(update, context):
    try:
        if len(str(float(update.message.text)).split('.')[-1]) > 2 or float(update.message.text) <= 0:
            int('придумали тут')
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
    reply_keyboard = [['Транспорт', 'Здоровье'], ['Кафе/Продукты', 'Развлечения']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text('На какую категорию вы хотите установить лимит?',
                                    reply_markup=markup)
    return 1


async def limcategor(update, context):
    if update.message.text in ['Транспорт', 'Здоровье', 'Кафе/Продукты', 'Развлечения']:
        context.user_data['category'] = update.message.text
        await update.message.reply_text('Какой лимит вы хотите установить?\n'
                                        'Напишите только сумму в рублях в формате "рубли.копейки".',
                                        reply_markup=ReplyKeyboardRemove())
        return 2
    await update.message.reply_text('На какую категорию вы хотите установить лимит?')
    return 1


async def limsum(update, context):
    try:
        if len(str(float(update.message.text)).split('.')[-1]) > 2 or float(update.message.text) <= 0:
            int('придумали тут')
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
    application.add_handler(CommandHandler("help", help))
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
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('rename', rename)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_nickname)]},
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
