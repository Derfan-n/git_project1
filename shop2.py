import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, Bot, ReplyKeyboardRemove
from config import BOT_TOKEN
import os

from data import db_session
from data.users import User
from data.products import Products

"""
    -пользаватель может добавить молоко в категорию книг или техники
    -сделать каректировку фото по размеру
    -при выключении ошибка -1 (из-за кнопок)
    -менять имя пользователя в бд (думаю не надо)
"""

# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
# logger = logging.getLogger(__name__)

TOKEN = BOT_TOKEN
bot = Bot(token=TOKEN)

reply_keyboard_cancel = [['Отмена']]

reply_keyboard = [['МЕНЮ', 'ТОВАРЫ']]

reply_keyboard_menu = [['КОРЗИНА', 'ИЗБРАННЫЕ ТОВАРЫ', 'МОИ ТОВАРЫ'],
                       ['ДОБАВИТЬ ТОВАР', 'НАЗАД']]

reply_keyboard_buy = [['продукты', 'техника', 'инструменты'],
                      ['книги', 'другое', 'НАЗАД']]

reply_keyboard_favorites_and_basket = [['ДОБАВИТЬ В КОРЗИНУ', 'ДОБАВИТЬ В ИЗБРАННОЕ', 'НАЗАД']]

reply_keyboard_add_product = [['ЗАКОНЧИТЬ ДОБАВЛЕНИЕ']]

markup_cancel = ReplyKeyboardMarkup(reply_keyboard_cancel, one_time_keyboard=False, resize_keyboard=True)
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
markup_menu = ReplyKeyboardMarkup(reply_keyboard_menu, one_time_keyboard=False, resize_keyboard=True)
markup_buy = ReplyKeyboardMarkup(reply_keyboard_buy, one_time_keyboard=False, resize_keyboard=True)
markup_add = ReplyKeyboardMarkup(reply_keyboard_add_product, one_time_keyboard=False, resize_keyboard=True)
markup_favorites_and_basket = ReplyKeyboardMarkup(
    reply_keyboard_favorites_and_basket, one_time_keyboard=False, resize_keyboard=True)

category_of_products = ['technic', 'food', 'book', 'tools', 'other']
dict_category_of_products = {'техника': 'technic',
                             'продукты': 'food',
                             'книги': 'book',
                             'инструменты': 'tools',
                             'другое': 'other'}
category_of_products_ru = ['продукты', 'техника', 'инструменты', 'книги', 'другое']

back_count = [0, 0, 0, 0]


def add_user(update, context):
    """Добавление с проверкой регистрации пользователя"""
    db_sess = db_session.create_session()
    already_added = False
    if len(db_sess.query(User).all()) == 0:
        user = User()
        if update.message.from_user.last_name is not None:
            user.user_name = f'{update.message.from_user.first_name} {update.message.from_user.last_name}'
        else:
            user.user_name = f'{update.message.from_user.first_name}'
        user.telegram_id = update.message.from_user.id
        db_sess.add(user)
        db_sess.commit()
        print("Вы успешно зарегистрированы")
    else:
        if update.message.from_user.last_name is not None:
            nickname = f'{update.message.from_user.first_name} {update.message.from_user.last_name}'
        else:
            nickname = f'{update.message.from_user.first_name}'
        telegram_user_id = update.message.from_user.id
        for username in db_sess.query(User).all():
            if username.telegram_id == str(telegram_user_id):
                already_added = True
        if already_added is False:
            user = User()
            user.user_name = nickname
            user.telegram_id = telegram_user_id
            db_sess.add(user)
            db_sess.commit()
            print("Вы успешно зарегистрированы")
        else:
            print("Вы уже зарегистрированы")


def start(update, context):
    db_session.global_init("db/shop_db.db")
    update.message.reply_text(f"Привет, {update.message.from_user.first_name}, я бот магазин", reply_markup=markup)
    add_user(update, context)


def menu(update, context):
    update.message.reply_text('МЕНЮ:', reply_markup=markup_menu)
    back_count[0] = 1
    print(back_count)


def basket(update, context):
    update.message.reply_text('Корзина:')
    db_sess = db_session.create_session()

    user = db_sess.query(User).filter(User.telegram_id == update.message.from_user.id).first()
    shopping_cart = list(map(int, str(user.shopping_cart).split(';')))
    """товары выводятся в порядке добавления"""
    for products_id in shopping_cart:
        for product in db_sess.query(Products).filter(Products.id == products_id):
            if product.image is not None:
                update.message.reply_photo(
                    photo=open(f"files/{product.image}", 'rb'),
                    caption=f"{product.title} \n"
                            f"{product.description} \n"
                            f"{product.cost}")
            else:
                update.message.reply_text(f"{product.title} \n"
                                          f"{product.description} \n"
                                          f"{product.cost}")


def selected_products(update, context):
    update.message.reply_text('Товары которые находятся в избранном:')
    db_sess = db_session.create_session()

    user = db_sess.query(User).filter(User.telegram_id == update.message.from_user.id).first()
    elected_products = list(map(int, str(user.elected_products).split(';')))
    """товары выводятся в порядке добавления"""
    for products_id in elected_products:
        for product in db_sess.query(Products).filter(Products.id == products_id):
            if product.image is not None:
                update.message.reply_photo(
                    photo=open(f"files/{product.image}", 'rb'),
                    caption=f"{product.title} \n"
                            f"{product.description} \n"
                            f"{product.cost}")
            else:
                update.message.reply_text(f"{product.title} \n"
                                          f"{product.description} \n"
                                          f"{product.cost}")


def user_products(update, context):
    """Показывает товары добавленные пользователем"""
    user_id = ''
    update.message.reply_text('Мои товары:', reply_markup=markup_menu)
    db_sess = db_session.create_session()
    for user in db_sess.query(User).filter(User.user_name == f'{update.message.from_user.first_name} '
                                                             f'{update.message.from_user.last_name}'):
        user_id = user.id
    for product in db_sess.query(Products).filter(Products.seller_id == user_id):
        if product.image is not None:
            update.message.reply_photo(
                photo=open(f"files/{product.image}", 'rb'),
                caption=f"{product.title} \n"
                        f"{product.description} \n"
                        f"{product.cost}")
        else:
            update.message.reply_text(f"{product.title} \n"
                                      f"{product.description} \n"
                                      f"{product.cost}")


def buy(update, context):
    update.message.reply_text('ТОВАРЫ:', reply_markup=markup_buy)
    back_count[1] = 1
    print(back_count)


added_product = ''

add_product_flag = 0
name_product = []
category_name = ''


def product(update, context):
    global add_product_flag, name_product, category_name
    """Показывает товары в категории technic"""
    if category_name not in category_of_products:
        category_name = dict_category_of_products[update.message.text]
    print(category_name)
    update.message.reply_text('Список товаров:', reply_markup=markup_cancel)
    product_names = []
    name_product = []
    db_sess = db_session.create_session()
    for product in db_sess.query(Products).filter(Products.category == category_name):
        product_names.append((product.title, product.cost))
    a = ''
    for i in product_names:
        name_product.append(i[0])
        b = str(i[0]) + ' - ' + str(i[1]) + '\n'
        a += str(b)
    update.message.reply_text(a)
    print(name_product)
    update.message.reply_text('напишите название товара который хотите посмотреть поподробней')
    add_product_flag = 1


def product_add(update, context):
    global add_product_flag, added_product, category_name
    added_product = update.message.text
    back_count[3] = 1
    if added_product != 'Отмена':
        update.message.reply_text('товар:', reply_markup=markup_favorites_and_basket)
        db_sess = db_session.create_session()
        for product in db_sess.query(Products).filter(Products.category == category_name):
            if product.title == update.message.text:
                if product.image is not None:
                    update.message.reply_photo(
                        photo=open(f"files/{product.image}", 'rb'),
                        caption=f"{product.title} \n"
                                f"{product.description} \n"
                                f"{product.cost}")
                else:
                    update.message.reply_text(f"{product.title} \n"
                                              f"{product.description} \n"
                                              f"{product.cost}")
    else:
        update.message.reply_text('ТОВАРЫ:', reply_markup=markup_buy)
        category_name = ''
        add_product_flag = 0
        back_count[3] = 0
    add_product_flag = 0


def add_to_basket(update, context):
    product_name = added_product
    db_sess = db_session.create_session()
    product_id = 0
    for product in db_sess.query(Products).filter(Products.title == product_name):
        product_id = product.id

    user = db_sess.query(User).filter(User.telegram_id == update.message.from_user.id).first()
    if user.shopping_cart is None:
        user.shopping_cart = product_id
    else:
        shopping_cart = []
        if len(str(user.shopping_cart)) > 1:
            for i in list(str(user.shopping_cart).split(';')):
                shopping_cart.append(i)
        else:
            shopping_cart.append(str(user.shopping_cart))
        if str(product_id) not in shopping_cart:
            shopping_cart.append(str(product_id))
            shopping_cart = ';'.join(shopping_cart)
            user.shopping_cart = shopping_cart
        else:
            update.message.reply_text('Товар уже есть в корзине')
    db_sess.commit()


def add_to_selected(update, context):
    product_name = added_product
    db_sess = db_session.create_session()
    product_id = 0
    for product in db_sess.query(Products).filter(Products.title == product_name):
        product_id = product.id

    user = db_sess.query(User).filter(User.telegram_id == update.message.from_user.id).first()
    if user.elected_products is None:
        user.elected_products = product_id
    else:
        elected_products = []
        if len(str(user.elected_products)) > 1:
            for i in list(str(user.elected_products).split(';')):
                elected_products.append(i)
        else:
            elected_products.append(str(user.elected_products))
        if str(product_id) not in elected_products:
            elected_products.append(str(product_id))
            shopping_cart = ';'.join(elected_products)
            user.elected_products = shopping_cart
        else:
            update.message.reply_text('Товар уже есть в избранном')
    db_sess.commit()


def back(update, context):
    if back_count[0] == 1:
        update.message.reply_text('Основное окно:', reply_markup=markup)
        back_count[0] = 0
        print(back_count)
    if back_count[1] == 1 and back_count[3] == 0:
        update.message.reply_text('Основное окно:', reply_markup=markup)
        back_count[1] = 0
        print(back_count)
    if back_count[3] == 1:
        product(update, context)
        back_count[3] = 0



def finish_adding(update, context):
    """Обработка кнопки 'ЗАКОНЧИТЬ ДОБАВЛЕНИЕ' """
    global step_add, add_par
    update.message.reply_text('Товар не добавлен', reply_markup=markup_menu)
    update.message.reply_text('МЕНЮ:', reply_markup=markup_menu)

    if file_name != '':
        os.remove(f"files/{file_name}")

    step_add = [0, 0, 0, 0, 0]
    add_par = 0
    back_count[2] = 0


def image_handler(update, context):
    """Зарузка фотографий"""
    global file_name
    db_sess = db_session.create_session()
    photo_id = 0
    for product in db_sess.query(Products).all():
        if product.id >= photo_id:
            photo_id = product.id

    file = update.message.photo[-1].file_id
    obj = context.bot.get_file(file)
    obj.download(f'files/test{photo_id + 1}.jpg')

    file_name = f"test{photo_id + 1}.jpg"

    update.message.reply_text("Фото успешно сохранено")


def add_product_to_db(product_name, cash, description, category, file_name, update, context):
    """Добаыление товара в дб"""
    print(product_name, cash, description, category, file_name)
    db_sess = db_session.create_session()

    user_id = ''
    for user in db_sess.query(User).filter(User.user_name == f'{update.message.from_user.first_name} '
                                                             f'{update.message.from_user.last_name}'):
        user_id = user.id
    """Проверка есть ли категория указанная пользователем среди заранее предусмотренных"""
    if category not in category_of_products:
        product_category = 'other'
    else:
        product_category = category

    prod = Products()
    prod.title = product_name
    prod.description = description
    prod.cost = cash
    prod.image = file_name
    prod.category = product_category
    prod.seller_id = user_id
    db_sess.add(prod)
    db_sess.commit()
    """проверить несколько добавлений подряд(это напоминание для меня)"""
    product_name = ''
    cash = ''
    description = ''
    category = ''
    file_name = ''
    update.message.reply_text('Товар успешно добавлен', reply_markup=markup_menu)
    update.message.reply_text('МЕНЮ:', reply_markup=markup_menu)
    back_count[2] = 0


add_par = 0
step_add = [0, 0, 0, 0, 0]
product_name = ''
cash = ''
description = ''
category = ''
file_name = ''


def add_product(update, context):
    global add_par
    update.message.reply_text('Добавление товара:', reply_markup=markup_add)
    back_count[2] = 1
    update.message.reply_text('Напишите название товара')
    add_par = 1


def add_product_add(update, context):
    """Некоректный ввод обработан, но если вместо фото отправить текст, то программа падает!!!(исправлю потом)"""
    global step_add, add_par, product_name, cash, description, category
    if step_add[0] == 0:
        product_name = update.message.text
        print(product_name)
        if product_name is not None:
            rename = False
            db_sess = db_session.create_session()
            for product in db_sess.query(Products).all():
                if product.title == product_name:
                    rename = True
            if rename is False:
                update.message.reply_text('Напишите описание')
                step_add[0] = 1
            else:
                update.message.reply_text('Товар с таким названием уже есть, пожалуйста напишите другое название')
        else:
            update.message.reply_text('Название не полученно, напите его повторно')

    elif step_add[1] == 0:
        description = update.message.text
        print(description)
        if description is not None:
            update.message.reply_text('Загрузите фото(фото должно быть сжатым) \n'
                                      '/если после отправки ничего не произошло, отправте другое фото/')
            step_add[1] = 1
        else:
            update.message.reply_text('Описание не полученно, напите его повторно')

    elif step_add[2] == 0:
        if isinstance(update.message.text, str) is not True:
            image_handler(update, context)
            update.message.reply_text('Выберите категорию товара: \n'
                                      'technic, food, tools, book, other \n'
                                      '/если ваша категория отсутствует, товар автоматически будет добавлен в "другое"/')
            step_add[2] = 1
        else:
            update.message.reply_text('Фото небыло полученно, отправте его снова, без каких-либо подписей')
    elif step_add[3] == 0:
        category = update.message.text
        print(category)
        if category is not None:
            update.message.reply_text('Напишите цену')
            step_add[3] = 1
        else:
            update.message.reply_text('Категория не полученна, напите её повторно')
    else:
        cash = update.message.text
        print(cash)
        if cash is not None:
            step_add = [0, 0, 0, 0, 0]
            add_par = 0
            add_product_to_db(product_name, cash, description, category, file_name, update, context)
        else:
            update.message.reply_text('Цена не полученна, напите её повторно')


def transition(update, context):
    if update.message.text == 'МЕНЮ':
        menu(update, context)
    elif update.message.text == 'КОРЗИНА':
        basket(update, context)
    elif update.message.text == 'ИЗБРАННЫЕ ТОВАРЫ':
        selected_products(update, context)
    elif update.message.text == 'МОИ ТОВАРЫ':
        user_products(update, context)
    elif update.message.text == 'ДОБАВИТЬ ТОВАР':
        add_product(update, context)
    elif update.message.text == 'ТОВАРЫ':
        buy(update, context)
    elif update.message.text in category_of_products_ru:
        product(update, context)
    elif update.message.text == 'МОИ ТОВАРЫ':
        user_products(update, context)
    elif update.message.text == 'НАЗАД':
        back(update, context)
    elif update.message.text == 'ЗАКОНЧИТЬ ДОБАВЛЕНИЕ':
        finish_adding(update, context)
    elif update.message.text == 'ДОБАВИТЬ В КОРЗИНУ':
        add_to_basket(update, context)
    elif update.message.text == 'КОРЗИНА':
        basket(update, context)
    elif update.message.text == 'ДОБАВИТЬ В ИЗБРАННОЕ':
        add_to_selected(update, context)
    elif update.message.text == 'ИЗБРАННЫЕ ТОВАРЫ':
        selected_products(update, context)
    # проверка на то что находимся мы сейчас в диологе добавления или нет
    elif add_par == 1:
        add_product_add(update, context)
    # проверка на то что находимся мы сейчас в диологе с выбором или нет
    elif add_product_flag == 1:
        if update.message.text in name_product or update.message.text == 'Отмена':
            product_add(update, context)
        else:
            update.message.reply_text('Вы ошиблись в названии напишити его снова')


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    text_handler = MessageHandler(Filters.text & ~Filters.command, transition)
    dp.add_handler(text_handler)
    """Это для загрузки фото"""
    dp.add_handler(MessageHandler(Filters.photo, add_product_add))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
