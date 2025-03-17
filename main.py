import telebot
from telebot import types

# Токен вашего бота
API_TOKEN = '8039802274:AAGfRrppM7Bkqx9hw4hY5U2bjjcaT79pL1Y'

# Инициализация бота
bot = telebot.TeleBot(API_TOKEN)

# ID администратора (замените на ваш Telegram ID)
ADMIN_ID = 217676895  # Пример ID администратора

# Пример данных о товарах с изображениями и ароматами
products = [
    {
        "id": 1,
        "name": "Товар 1",
        "price": 100,
        "image_url": "https://vchemraznica.ru/wp-content/uploads/2019/01/soap22.jpg",
        "scents": ["Аромат 1", "Аромат 2", "Аромат 3"]  # Список ароматов
    },
    {
        "id": 2,
        "name": "Товар 2",
        "price": 200,
        "image_url": "https://vchemraznica.ru/wp-content/uploads/2019/01/soap22.jpg",
        "scents": ["Аромат A", "Аромат B"]
    },
    {
        "id": 3,
        "name": "Товар 3",
        "price": 300,
        "image_url": "https://vchemraznica.ru/wp-content/uploads/2019/01/soap22.jpg",
        "scents": ["Аромат X", "Аромат Y", "Аромат Z"]
    },
]

# Словарь для хранения корзин пользователей
user_carts = {}

# Словарь для хранения текущего индекса товара в каталоге для каждого пользователя
user_product_index = {}

# Словарь для хранения данных о заказе
user_order_data = {}

# Словарь для хранения временных данных о количестве товара и выборе аромата
temp_data = {}

# Словарь для хранения данных о добавлении товара администратором
admin_temp_data = {}

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_product_index[user_id] = 0  # Начинаем с первого товара
    show_product(message.chat.id, user_id)

# Показать товар
def show_product(chat_id, user_id):
    index = user_product_index[user_id]
    product = products[index]

    # Создаем inline-клавиатуру
    markup = types.InlineKeyboardMarkup()
    add_to_cart_button = types.InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add_{product['id']}")
    next_button = types.InlineKeyboardButton(text="➡️ Следующий товар", callback_data="next_product")
    prev_button = types.InlineKeyboardButton(text="⬅️ Предыдущий товар", callback_data="prev_product")
    cart_button = types.InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")

    markup.row(add_to_cart_button)
    markup.row(prev_button, next_button)
    markup.row(cart_button)

    # Отправляем фото товара с описанием и кнопками
    bot.send_photo(
        chat_id,
        photo=product['image_url'],
        caption=f"{product['name']}\nЦена: {product['price']} руб.",
        reply_markup=markup
    )

# Обработка нажатий на inline-кнопки
@bot.callback_query_handler(func=lambda call: True)
def process_callback(call):
    user_id = call.from_user.id

    if call.data.startswith('add_'):
        # Запрос количества товара
        product_id = int(call.data.split('_')[1])
        temp_data[user_id] = {"product_id": product_id, "step": "quantity"}
        bot.send_message(call.message.chat.id, "Введите количество товара:", reply_markup=types.ForceReply())
        bot.answer_callback_query(call.id)

    elif call.data == "next_product":
        # Переход к следующему товару
        user_product_index[user_id] = (user_product_index[user_id] + 1) % len(products)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_product(call.message.chat.id, user_id)

    elif call.data == "prev_product":
        # Переход к предыдущему товару
        user_product_index[user_id] = (user_product_index[user_id] - 1) % len(products)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_product(call.message.chat.id, user_id)

    elif call.data == "view_cart":
        # Просмотр корзины
        if user_id in user_carts and user_carts[user_id]:
            cart_items = "\n".join([f"{p['name']} ({p['scent']}) - {p['quantity']} шт. x {p['price']} руб. = {p['quantity'] * p['price']} руб." for p in user_carts[user_id]])
            total_price = sum(p['quantity'] * p['price'] for p in user_carts[user_id])

            # Создаем клавиатуру для управления корзиной
            markup = types.InlineKeyboardMarkup()
            for index, item in enumerate(user_carts[user_id]):
                change_scent_button = types.InlineKeyboardButton(text=f"✏️ Изменить аромат ({item['name']})", callback_data=f"change_scent_{index}")
                markup.add(change_scent_button)
            clear_button = types.InlineKeyboardButton(text="❌ Очистить корзину", callback_data="clear_cart")
            checkout_button = types.InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")
            markup.add(clear_button, checkout_button)

            bot.send_message(
                call.message.chat.id,
                f"Ваша корзина:\n{cart_items}\n\nОбщая сумма: {total_price} руб.",
                reply_markup=markup
            )
        else:
            bot.answer_callback_query(call.id, "Ваша корзина пуста.", show_alert=True)

    elif call.data.startswith("change_scent_"):
        # Изменение аромата в корзине
        index = int(call.data.split('_')[2])
        if user_id in user_carts and index < len(user_carts[user_id]):
            product_id = user_carts[user_id][index]["id"]
            product = next((p for p in products if p['id'] == product_id), None)
            if product and "scents" in product:
                markup = types.InlineKeyboardMarkup()
                for scent in product["scents"]:
                    markup.add(types.InlineKeyboardButton(text=scent, callback_data=f"update_scent_{index}_{scent}"))
                bot.send_message(call.message.chat.id, "Выберите новый аромат:", reply_markup=markup)
            else:
                bot.send_message(call.message.chat.id, "Ароматы для этого товара не найдены.")
        else:
            bot.send_message(call.message.chat.id, "Товар не найден в корзине.")

    elif call.data.startswith("update_scent_"):
        # Обновление аромата в корзине
        parts = call.data.split('_')
        index = int(parts[2])
        scent = '_'.join(parts[3:])  # Аромат может содержать символы подчеркивания
        if user_id in user_carts and index < len(user_carts[user_id]):
            user_carts[user_id][index]["scent"] = scent
            bot.answer_callback_query(call.id, f"Аромат изменен на: {scent}")
            bot.send_message(call.message.chat.id, f"Аромат изменен на: {scent}")
        else:
            bot.answer_callback_query(call.id, "Ошибка при изменении аромата.")

    elif call.data == "clear_cart":
        # Очистка корзины
        if user_id in user_carts:
            user_carts[user_id].clear()
            bot.answer_callback_query(call.id, "Корзина очищена.")
            bot.send_message(call.message.chat.id, "Ваша корзина очищена.")
        else:
            bot.answer_callback_query(call.id, "Ваша корзина уже пуста.", show_alert=True)

    elif call.data == "checkout":
        # Оформление заказа
        if user_id in user_carts and user_carts[user_id]:
            # Запрашиваем имя
            bot.send_message(call.message.chat.id, "Введите ваше имя:", reply_markup=types.ForceReply())
            user_order_data[user_id] = {"step": "name"}
        else:
            bot.answer_callback_query(call.id, "Ваша корзина пуста. Добавьте товары для оформления заказа.", show_alert=True)

# Обработка текстовых сообщений (для формы оформления заказа, количества товара и выбора аромата)
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id

    if user_id in temp_data:
        step = temp_data[user_id].get("step")

        if step == "quantity":
            # Обработка количества товара
            try:
                quantity = int(message.text)
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                bot.send_message(message.chat.id, "Пожалуйста, введите корректное количество (целое число больше 0).")
                return

            temp_data[user_id]["quantity"] = quantity
            temp_data[user_id]["step"] = "scent"

            # Запрашиваем выбор аромата
            product_id = temp_data[user_id]["product_id"]
            product = next((p for p in products if p['id'] == product_id), None)

            if product and "scents" in product:
                markup = types.InlineKeyboardMarkup()
                for scent in product["scents"]:
                    markup.add(types.InlineKeyboardButton(text=scent, callback_data=f"scent_{scent}"))
                bot.send_message(message.chat.id, "Выберите аромат:", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "Ароматы для этого товара не найдены.")
                temp_data.pop(user_id)

        elif step == "scent":
            # Обработка выбора аромата
            scent = message.text
            product_id = temp_data[user_id]["product_id"]
            quantity = temp_data[user_id]["quantity"]

            product = next((p for p in products if p['id'] == product_id), None)

            if product:
                if user_id not in user_carts:
                    user_carts[user_id] = []
                # Проверяем, есть ли товар уже в корзине
                existing_item = next((item for item in user_carts[user_id] if item['id'] == product_id and item['scent'] == scent), None)
                if existing_item:
                    existing_item['quantity'] += quantity
                else:
                    user_carts[user_id].append({
                        "id": product_id,
                        "name": product['name'],
                        "price": product['price'],
                        "quantity": quantity,
                        "scent": scent  # Добавляем выбранный аромат
                    })
                bot.send_message(message.chat.id, f"Товар {product['name']} (аромат: {scent}) в количестве {quantity} шт. добавлен в корзину.")
            else:
                bot.send_message(message.chat.id, "Товар не найден.")

            # Очищаем временные данные
            temp_data.pop(user_id)

            # Показываем каталог товаров снова
            show_product(message.chat.id, user_id)

    elif user_id in user_order_data:
        step = user_order_data[user_id].get("step")

        if step == "name":
            # Сохраняем имя
            user_order_data[user_id]["name"] = message.text
            user_order_data[user_id]["step"] = "phone"
            bot.send_message(message.chat.id, "Введите ваш номер телефона:", reply_markup=types.ForceReply())

        elif step == "phone":
            # Сохраняем телефон
            user_order_data[user_id]["phone"] = message.text
            user_order_data[user_id]["step"] = "address"
            bot.send_message(message.chat.id, "Введите ваш адрес доставки:", reply_markup=types.ForceReply())

        elif step == "address":
            # Сохраняем адрес
            user_order_data[user_id]["address"] = message.text
            user_order_data[user_id]["step"] = "complete"

            # Формируем заказ
            cart_items = "\n".join([f"{p['name']} ({p['scent']}) - {p['quantity']} шт. x {p['price']} руб. = {p['quantity'] * p['price']} руб." for p in user_carts[user_id]])
            total_price = sum(p['quantity'] * p['price'] for p in user_carts[user_id])

            order_info = (
                f"Ваш заказ:\n{cart_items}\n\n"
                f"Общая сумма: {total_price} руб.\n\n"
                f"Имя: {user_order_data[user_id]['name']}\n"
                f"Телефон: {user_order_data[user_id]['phone']}\n"
                f"Адрес: {user_order_data[user_id]['address']}"
            )

            # Отправляем уведомление администратору
            admin_message = (
                f"Новый заказ!\n\n"
                f"Детали заказа:\n{cart_items}\n\n"
                f"Общая сумма: {total_price} руб.\n\n"
                f"Имя: {user_order_data[user_id]['name']}\n"
                f"Телефон: {user_order_data[user_id]['phone']}\n"
                f"Адрес: {user_order_data[user_id]['address']}"
            )
            bot.send_message(ADMIN_ID, admin_message)

            # Создаем клавиатуру для оплаты
            markup = types.InlineKeyboardMarkup()
            pay_button = types.InlineKeyboardButton(text="💳 Оплатить заказ", callback_data="pay_order")
            markup.add(pay_button)

            bot.send_message(message.chat.id, order_info, reply_markup=markup)

    elif user_id == ADMIN_ID and user_id in admin_temp_data:
        # Обработка добавления товара администратором
        step = admin_temp_data[user_id].get("step")

        if step == "name":
            admin_temp_data[user_id]["name"] = message.text
            admin_temp_data[user_id]["step"] = "price"
            bot.send_message(message.chat.id, "Введите цену товара:", reply_markup=types.ForceReply())

        elif step == "price":
            try:
                price = int(message.text)
                if price <= 0:
                    raise ValueError
            except ValueError:
                bot.send_message(message.chat.id, "Пожалуйста, введите корректную цену (целое число больше 0).")
                return

            admin_temp_data[user_id]["price"] = price
            admin_temp_data[user_id]["step"] = "image_url"
            bot.send_message(message.chat.id, "Отправьте URL изображения товара:", reply_markup=types.ForceReply())

        elif step == "image_url":
            admin_temp_data[user_id]["image_url"] = message.text
            admin_temp_data[user_id]["step"] = "scents"
            bot.send_message(message.chat.id, "Введите ароматы через запятую (например, Аромат 1, Аромат 2):", reply_markup=types.ForceReply())

        elif step == "scents":
            scents = [scent.strip() for scent in message.text.split(",")]
            admin_temp_data[user_id]["scents"] = scents

            # Создаем новый товар
            new_product = {
                "id": len(products) + 1,
                "name": admin_temp_data[user_id]["name"],
                "price": admin_temp_data[user_id]["price"],
                "image_url": admin_temp_data[user_id]["image_url"],
                "scents": scents
            }
            products.append(new_product)

            bot.send_message(message.chat.id, f"Товар '{new_product['name']}' успешно добавлен!")
            admin_temp_data.pop(user_id)

# Обработка выбора аромата
@bot.callback_query_handler(func=lambda call: call.data.startswith('scent_'))
def process_scent_selection(call):
    user_id = call.from_user.id
    scent = call.data.split('_')[1]

    if user_id in temp_data:
        temp_data[user_id]["scent"] = scent
        bot.send_message(call.message.chat.id, f"Вы выбрали аромат: {scent}. Теперь введите количество товара:", reply_markup=types.ForceReply())
        bot.answer_callback_query(call.id)

# Обработка оплаты заказа
@bot.callback_query_handler(func=lambda call: call.data == "pay_order")
def process_payment(call):
    user_id = call.from_user.id

    # Формируем сообщение с подтверждением заказа
    if user_id in user_carts and user_carts[user_id]:
        cart_items = "\n".join([f"{p['name']} ({p['scent']}) - {p['quantity']} шт. x {p['price']} руб. = {p['quantity'] * p['price']} руб." for p in user_carts[user_id]])
        total_price = sum(p['quantity'] * p['price'] for p in user_carts[user_id])

        order_info = (
            f"Ваш заказ успешно оформлен!\n\n"
            f"Детали заказа:\n{cart_items}\n\n"
            f"Общая сумма: {total_price} руб.\n\n"
            f"Имя: {user_order_data[user_id]['name']}\n"
            f"Телефон: {user_order_data[user_id]['phone']}\n"
            f"Адрес: {user_order_data[user_id]['address']}"
        )

        # Отправляем сообщение с подтверждением заказа пользователю
        bot.send_message(call.message.chat.id, order_info)

        # Очищаем корзину и данные о заказе
        if user_id in user_carts:
            user_carts[user_id].clear()
        if user_id in user_order_data:
            user_order_data.pop(user_id)

        # Оповещение об успешной оплате
        bot.answer_callback_query(call.id, "Оплата прошла успешно! Спасибо за заказ.")
    else:
        bot.answer_callback_query(call.id, "Ваша корзина пуста.", show_alert=True)

# Команда для добавления товара администратором
@bot.message_handler(commands=['add_product'])
def add_product(message):
    if message.from_user.id == ADMIN_ID:
        admin_temp_data[message.from_user.id] = {"step": "name"}
        bot.send_message(message.chat.id, "Введите название товара:", reply_markup=types.ForceReply())
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")

# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)

#import telebot
#bot = telebot.TeleBot('7017372065:AAF6IBI_IeNPRPKJ6gMUpmkp9jfCMF3zsMg')

#@bot.message_handler(commands=['start','main','hello'])
#def main(message):
#    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} {message.from_user.last_name} добро пожаловать в бот для оплаты заказа')
#bot.polling(none_stop=True)