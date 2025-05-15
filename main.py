import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
from configs import TOKEN
import sqlite3
from flask import Flask
from data import db_session
from data.users import User
from data.expenses import Expenses
from datetime import *
from make_diagramme import stat_img
from get_banks import find_bank

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='logging.log', level=logging.DEBUG)

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


async def start(update, context):
    db_sess = db_session.create_session()
    name = update.message.from_user.username
    res = db_sess.query(User).filter(User.username == name).first()
    if not res:
        new = User()
        new.username = name
        new.nickname = name
        db_sess.add(new)
        db_sess.commit()
    user = db_sess.query(User).filter(User.username == name).first()
    reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text(f'Здравствуйте, {user.nickname}\n'
                                    f'с помощью /help вы можете узнать мой функционал', reply_markup=markup)


async def help(update, context):
    db_sess = db_session.create_session()
    name = update.message.from_user.username
    user = db_sess.query(User).filter(User.username == name).first()
    await update.message.reply_text(
        f'\n'
        f'Вот список команд для работы с ботом: \n'
        f'\n'
        f'/rename - установите, как к вам будет обращаться бот.\n'
        f'/stop - возвращение в главное меню.\n'
        f'/add - добавить данные о платеже.\n'
        f'/lim - установить лимит на траты по категории.\n'
        f'/unset - отменить регулярные платежи в категории.\n'
        f'/clear - очистить все данные пользователя.\n'
        f'/get_statistic - получить отчет о тратах по категориям.\n'
        f'/get_banks - получить карту с 10 ближайшими к введенному месту банкоматами.\n'
        f'/reset_expenses - сбросить сумму текущих расходов по вашему усмотрению. '
    )


async def reset_expenses(update, context):
    db_sess = db_session.create_session()
    name = update.message.from_user.username
    user = db_sess.query(User).filter(User.username == name).first()
    id = user.id
    con = sqlite3.connect('db/finance.db')
    cur = con.cursor()
    cur.execute("UPDATE expenses SET sum = '0'  WHERE users_id = ? ", (id,))
    con.commit()
    db_sess.commit()
    await update.message.reply_text(f'К новым тратам! Дальше - больше ;)')
    return ConversationHandler.END


async def get_banks(update, context):
    name = update.message.from_user.username
    db_sess = db_session.create_session()
    await update.message.reply_text(f'Введите адрес, рядом с которым хотите узнать расположение банкоматов.\n'
                                    f'<город> <улица> <дом>')
    return 1


async def ret_banks_img(update, context):
    address = update.message.text
    find_bank(address)
    chat_id = update.effective_message.chat_id
    photo = open('static/img/map.png', 'rb')
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=f'10 ближайших банкоматов к {address}'
    )
    return ConversationHandler.END


async def get_statistic(update, context):
    db_sess = db_session.create_session()
    name = update.message.from_user.username
    user = db_sess.query(User).filter(User.username == name).first()
    if not user:
        reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text('По-видимому, мы еще не знакомы, давайте познакомимся командой /start',
                                        reply_markup=markup)
    else:
        id = user.id
        con = sqlite3.connect('db/finance.db')
        cur = con.cursor()
        result = cur.execute(f"""SELECT category, sum FROM expenses
                        WHERE users_id = {id}""").fetchall()
        stat_img(result)
        chat_id = update.effective_message.chat_id
        photo = open('static/img/stat.png', 'rb')
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption='Ваши расходы по категориям'
        )


async def clear(update, context):
    db_sess = db_session.create_session()
    name = update.message.from_user.username
    user = db_sess.query(User).filter(User.username == name).first()
    id = user.id
    con = sqlite3.connect('db/finance.db')
    cur = con.cursor()
    cur.execute("DELETE FROM expenses WHERE users_id = ?", (id,))
    con.commit()
    db_sess.delete(user)
    db_sess.commit()
    await update.message.reply_text(f'Теперь мы незнакомы :(')


async def rename(update, context):
    name = update.message.from_user.username
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.username == name).first()
    await update.message.reply_text(f'Как к вам обращаться, {user.nickname}?')
    return 1


async def set_nickname(update, context):
    name = update.message.from_user.username
    nickname = update.message.text
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.username == name).first()
    user.nickname = nickname
    db_sess.commit()
    await update.message.reply_text(f'Теперь вы для меня {user.nickname}! :)')
    return ConversationHandler.END


async def add(update, context):
    db_sess = db_session.create_session()
    name = update.message.from_user.username
    user = db_sess.query(User).filter(User.username == name).first()
    if not user:
        reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text('По-видимому, мы еще не знакомы, давайте познакомимся командой /start',
                                        reply_markup=markup)
        return ConversationHandler.END
    reply_keyboard = [['Добавить единоразовую трату'], ['Добавить регулярную трату'], ['/stop']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text('Вы хотите добавить регулярную трату или единоразовую?', reply_markup=markup)
    return 1


async def add1(update, context):
    reply_keyboard = [['Транспорт', 'Здоровье'], ['Кафе/Продукты', 'Развлечения'], ['Другое', '/stop']]
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
    if update.message.text in ['Транспорт', 'Здоровье', 'Кафе/Продукты', 'Развлечения', 'Другое']:
        reply_keyboard = [['/stop']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        context.user_data['category'] = update.message.text
        await update.message.reply_text('Какую сумму вы потратили?\n'
                                        'Напишите только сумму в рублях в формате "рубли.копейки".',
                                        reply_markup=markup)
        return 4
    await update.message.reply_text('Выберите к какой категории она относится.')
    return 2


async def add_one_sum(update, context):
    try:
        if len(str(float(update.message.text)).split('.')[-1]) > 2 or float(update.message.text) <= 0:
            int('придумали тут')
        db_sess = db_session.create_session()
        name = update.message.from_user.username
        user = db_sess.query(User).filter(User.username == name).first()
        usid = user.id
        cteg = db_sess.query(Expenses).filter(Expenses.users_id == usid,
                                              Expenses.category == context.user_data['category']).first()
        if not cteg:
            new = Expenses()
            new.users_id = usid
            new.category = context.user_data['category']
            new.sum = float(update.message.text)
            db_sess.add(new)
            db_sess.commit()
            reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            await update.message.reply_text('Готово!\n'
                                            'Если хотите добавить лимит на категорию, напишите /lim.',
                                            reply_markup=markup)
        else:
            if cteg.lim and cteg.sum + float(update.message.text) > cteg.lim:
                reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
                await update.message.reply_text(
                    f'Мы не можем добавить расход к общей сумме, так как он превышает лимит на'
                    f' {cteg.sum + float(update.message.text) - cteg.lim} рублей.\n'
                    f'Для начала поменяйте его командой /lim.',
                    reply_markup=markup)
            else:
                cteg.sum += float(update.message.text)
                reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
                await update.message.reply_text('Готово!',
                                                reply_markup=markup)
                db_sess.commit()
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text('Какую сумму вы потратили?\n'
                                        'Напишите только сумму в рублях в формате "рубли.копейки".')
        return 4


async def add_regular(update, context):
    if update.message.text in ['Транспорт', 'Здоровье', 'Кафе/Продукты', 'Развлечения', 'Другое']:
        reply_keyboard = [['/stop']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        context.user_data['category'] = update.message.text
        await update.message.reply_text('Когда был/будет первый платеж?\n'
                                        'Напишите только дату и время в формате "гггг-мм-дд чч:мм:сс".',
                                        reply_markup=markup)
        return 5
    await update.message.reply_text('Выберите к какой категории она относится.')
    return 3


async def regular_per(update, context):
    try:
        dt = update.message.text.split()
        dt = datetime.combine(date(int(dt[0].split('-')[0]), int(dt[0].split('-')[1]), int(dt[0].split('-')[2])),
                              time(int(dt[1].split(':')[0]), int(dt[1].split(':')[1]), int(dt[1].split(':')[2])))
        context.user_data['dt'] = dt
        await update.message.reply_text('На какую сумму и с какой периодичностью будут происходить платежи?\n'
                                        'Напишите только сумму в рублях и периодичность в днях в формате'
                                        ' "рубли.копейки дни".')
        return 6
    except Exception:
        await update.message.reply_text('Когда был/будет первый платеж?\n'
                                        'Напишите только дату и время в формате "гггг-мм-дд чч:мм:сс".')
        return 5


async def regular_sum(update, context):
    try:
        sad = update.message.text.split()
        if (len(str(float(sad[0])).split('.')[-1]) > 2 or float(sad[0]) <= 0
                or int(sad[1]) <= 0):
            int('придумали тут')
        db_sess = db_session.create_session()
        name = update.message.from_user.username
        user = db_sess.query(User).filter(User.username == name).first()
        usid = user.id
        cteg = db_sess.query(Expenses).filter(Expenses.users_id == usid,
                                              Expenses.category == context.user_data['category']).first()
        if not cteg:
            new = Expenses()
            new.users_id = usid
            new.category = context.user_data['category']
            new.regular = True
            new.first_regular = context.user_data['dt']
            new.period = int(sad[1])
            new.sum_regular = float(sad[0])
            db_sess.add(new)
            db_sess.commit()
        else:
            cteg.regular = True
            cteg.first_regular = context.user_data['dt']
            cteg.period = int(sad[1])
            cteg.sum_regular = float(sad[0])
            db_sess.commit()
        timer = context.user_data['dt'] - datetime.now() + timedelta(days=(int(sad[1])))
        while timer.total_seconds() <= 0:
            timer += timedelta(days=(int(sad[1])))
        chat_id = update.effective_message.chat_id
        remove_job_if_exists(context.user_data['category'] + str(usid), context)
        context.job_queue.run_once(task, timer.total_seconds(), chat_id=chat_id,
                                   name=context.user_data['category'] + str(usid),
                                   data=timer.total_seconds())
        reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text('Готово!',
                                        reply_markup=markup)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text('На какую сумму и с какой периодичностью будут происходить платежи?\n'
                                        'Напишите только сумму в рублях и периодичность в днях в формате'
                                        ' "рубли.копейки дни".')
        return 6


async def task(context):
    await context.bot.send_message(context.job.chat_id, text=f'Сегодня у вас назначен плановый платеж, не забудьте;)\n'
                                                             f'если хотите продолжать получать регулярные платежи, напи'
                                                             f'шите сегодня команду /repeat и категорию через пробел')


async def repeat(update, context):
    try:
        db_sess = db_session.create_session()
        name = update.message.from_user.username
        user = db_sess.query(User).filter(User.username == name).first()
        usid = user.id
        cteg = db_sess.query(Expenses).filter(Expenses.users_id == usid,
                                              Expenses.category == update.message.text.split()[1]).first()
        if cteg and not context.job_queue.get_jobs_by_name(update.message.text.split()[1] + str(usid)):
            timer = cteg.first_regular.date() - datetime.now().date() + timedelta(days=cteg.period)
            while timer.total_seconds() <= 0:
                timer += timedelta(days=cteg.period)
            if timer.days == timedelta(days=cteg.period).days:
                chat_id = update.effective_message.chat_id
                remove_job_if_exists(update.message.text.split()[1] + str(usid), context)
                context.job_queue.run_once(task, timer.total_seconds(), chat_id=chat_id,
                                           name=update.message.text.split()[1] + str(usid),
                                           data=timer.total_seconds())
                await update.message.reply_text('Готово!')
        else:
            await update.message.reply_text('У вас нет платежей, требуемых продолжение в этой категории')
    except Exception:
        await update.message.reply_text('Неверный формат')


def remove_job_if_exists(name, context):
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def unset(update, context):
    db_sess = db_session.create_session()
    name = update.message.from_user.username
    user = db_sess.query(User).filter(User.username == name).first()
    if not user:
        reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text('По-видимому, мы еще не знакомы, давайте познакомимся командой /start',
                                        reply_markup=markup)
        return ConversationHandler.END
    reply_keyboard = [['Транспорт', 'Здоровье'], ['Кафе/Продукты', 'Развлечения'], ['Другое', '/stop']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text('К какой категории относится регулярный платеж?',
                                    reply_markup=markup)
    return 1


async def unsetcateg(update, context):
    if update.message.text in ['Транспорт', 'Здоровье', 'Кафе/Продукты', 'Развлечения', 'Другое']:
        db_sess = db_session.create_session()
        name = update.message.from_user.username
        user = db_sess.query(User).filter(User.username == name).first()
        usid = user.id
        cteg = db_sess.query(Expenses).filter(Expenses.users_id == usid,
                                              Expenses.category == update.message.text).first()
        if not cteg or not cteg.first_regular:
            reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            await update.message.reply_text('У вас нет регулярных платежей в этой категории', reply_markup=markup)
            return ConversationHandler.END
        cteg.regular = False
        cteg.first_regular = None
        cteg.period = None
        cteg.sum_regular = None
        db_sess.commit()
        remove_job_if_exists(update.message.text + str(usid), context)
        text = f'Регулярные платежи отменены в категории {update.message.text}'
        reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(text, reply_markup=markup)
        return ConversationHandler.END
    await update.message.reply_text('Выберите к какой категории она относится.')
    return 1


async def lim(update, context):
    db_sess = db_session.create_session()
    name = update.message.from_user.username
    user = db_sess.query(User).filter(User.username == name).first()
    if not user:
        reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text('По-видимому, мы еще не знакомы, давайте познакомимся командой /start',
                                        reply_markup=markup)
        return ConversationHandler.END
    reply_keyboard = [['Транспорт', 'Здоровье'], ['Кафе/Продукты', 'Развлечения'], ['Другое', '/stop']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text('На какую категорию вы хотите установить лимит?',
                                    reply_markup=markup)
    return 1


async def limcategor(update, context):
    if update.message.text in ['Транспорт', 'Здоровье', 'Кафе/Продукты', 'Развлечения', 'Другое']:
        reply_keyboard = [['/stop']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        context.user_data['category'] = update.message.text
        await update.message.reply_text('Какой лимит вы хотите установить?\n'
                                        'Напишите только сумму в рублях в формате "рубли.копейки".',
                                        reply_markup=markup)
        return 2
    await update.message.reply_text('На какую категорию вы хотите установить лимит?')
    return 1


async def limsum(update, context):
    try:
        if len(str(float(update.message.text)).split('.')[-1]) > 2 or float(update.message.text) <= 0:
            int('придумали тут')
        db_sess = db_session.create_session()
        name = update.message.from_user.username
        user = db_sess.query(User).filter(User.username == name).first()
        usid = user.id
        cteg = db_sess.query(Expenses).filter(Expenses.users_id == usid,
                                              Expenses.category == context.user_data['category']).first()
        if not cteg:
            new = Expenses()
            new.users_id = usid
            new.category = context.user_data['category']
            new.lim = float(update.message.text)
            db_sess.add(new)
            db_sess.commit()
        else:
            if cteg.sum > float(update.message.text):
                await update.message.reply_text('Данная сумма больше той, которую вы уже потратили\n'
                                                'Напишите другую сумму в рублях в формате "рубли.копейки".')
                return 2
            else:
                cteg.lim = float(update.message.text)
                db_sess.commit()
        reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text('Готово!',
                                        reply_markup=markup)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text('Какой лимит вы хотите установить?\n'
                                        'Напишите только сумму в рублях в формате "рубли.копейки".')
        return 2


async def stop(update, context):
    reply_keyboard = [['/add', '/unset'], ['/lim', '/clear'], ['/get_statistic', '/get_banks']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text("Ну, ладно", reply_markup=markup)
    return ConversationHandler.END


def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("get_statistic", get_statistic))
    application.add_handler(CommandHandler("repeat", repeat))
    application.add_handler(CommandHandler("reset_expenses", reset_expenses))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add1)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_one)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_regular)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_one_sum)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, regular_per)],
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, regular_sum)]},
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
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('get_banks', get_banks)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ret_banks_img)]},
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(conv_handler)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('unset', unset)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, unsetcateg)]},
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    db_session.global_init("db/finance.db")
    main()
