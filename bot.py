import asyncio 
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from database import (
init_db,
create_order,
get_user_orders,
get_all_orders,
update_order_status,
get_order,
cancel_order,
get_statistics,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6901427267

dp = Dispatcher()


# Состояния создания заказа
class OrderForm(StatesGroup):
    waiting_for_product = State()
    waiting_for_price = State()
    waiting_for_quantity = State()


# Главное меню
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🛒 Создать заказ"),
            KeyboardButton(text="📦 Мои заказы"),
        ],
        [
            KeyboardButton(text="ℹ️ Помощь"),
        ],
    ],
    resize_keyboard=True,
)


@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "Привет! 👋\n\n"
        "Я бот для управления заказами.\n"
        "Выбери действие:",
        reply_markup=main_keyboard,
    )


# Начало создания заказа
@dp.message(lambda message: message.text == "🛒 Создать заказ")
async def create_order_handler(message: Message, state: FSMContext):
    await state.set_state(OrderForm.waiting_for_product)

    await message.answer(
        "🛒 Создание заказа\n\n"
        "Напиши название товара:"
    )

# Получаем товар
@dp.message(OrderForm.waiting_for_product)
async def get_product(message: Message, state: FSMContext):
    await state.update_data(product=message.text)

    await state.set_state(OrderForm.waiting_for_price)

    await message.answer(
        f"Товар: {message.text}\n\n"
        "Теперь введи цену за одну единицу в гривнах:"
    )


# Получаем цену
@dp.message(OrderForm.waiting_for_price)
async def get_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(
            "❌ Цена должна быть числом.\n"
            "Например: 1200 или 1200.50"
        )
        return

    if price <= 0:
        await message.answer(
            "❌ Цена должна быть больше нуля."
        )
        return

    await state.update_data(price=price)

    await state.set_state(OrderForm.waiting_for_quantity)

    await message.answer(
        "Теперь введи количество:"
    )
# Получаем количество
@dp.message(OrderForm.waiting_for_quantity)
async def get_quantity(message: Message, state: FSMContext):
    # Проверяем количество
    if not message.text or not message.text.isdigit():
        await message.answer(
            "❌ Количество должно быть целым числом.\n"
            "Например: 2"
        )
        return

    quantity = int(message.text)

    if quantity <= 0:
        await message.answer(
            "❌ Количество должно быть больше нуля."
        )
        return

    # Получаем данные из FSM
    data = await state.get_data()

    product = data["product"]
    price = data["price"]

    # Считаем итоговую стоимость
    total = price * quantity

    # Сохраняем заказ в БД
    order_id = create_order(
        user_id=message.from_user.id,
        product=product,
        price=price,
        quantity=quantity,
    )

    # Очищаем состояние пользователя
    await state.clear()

    # Кнопки для администратора
    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟡 В работу",
                    callback_data=f"status:processing:{order_id}",
                ),
                InlineKeyboardButton(
                    text="🟢 Завершить",
                    callback_data=f"status:completed:{order_id}",
                ),
            ]
        ]
    )

    # Уведомляем администратора
    await message.bot.send_message(
        ADMIN_ID,
        f"🔔 НОВЫЙ ЗАКАЗ #{order_id}\n\n"
        f"Товар: {product}\n"
        f"Цена: {price:.2f} грн\n"
        f"Количество: {quantity}\n"
        f"💰 Итого: {total:.2f} грн\n\n"
        f"👤 User ID: {message.from_user.id}\n"
        f"Статус: 🆕 Новый",
        reply_markup=admin_keyboard,
    )
    # Подтверждение клиенту
    await message.answer(
        "✅ Заказ сохранён!\n\n"
        f"📦 Заказ #{order_id}\n"
        f"Товар: {product}\n"
        f"Цена: {price:.2f} грн\n"
        f"Количество: {quantity}\n"
        f"💰 Итого: {total:.2f} грн"
    )
# Помощь
@dp.message(lambda message: message.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    await message.answer(
        "ℹ️ Помощь\n\n"
        "🛒 Создать заказ — создать новый заказ\n"
        "📦 Мои заказы — посмотреть свои заказы"
    )

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа.")
        return

    orders = get_all_orders()

    if not orders:
        await message.answer("📦 Заказов пока нет.")
        return

    for order_id, user_id, product, quantity, status in orders:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🟡 В работу",
                        callback_data=f"status:processing:{order_id}",
                    ),
                    InlineKeyboardButton(
                        text="🟢 Завершить",
                        callback_data=f"status:completed:{order_id}",
                    ),
                ]
            ]
        )

        await message.answer(
            f"📦 Заказ #{order_id}\n\n"
            f"Товар: {product}\n"
            f"Количество: {quantity}\n"
            f"User ID: {user_id}\n"
            f"Статус: {status}",
            reply_markup=keyboard,
        )
@dp.callback_query(lambda callback: callback.data.startswith("cancel:"))
async def cancel_order_handler(callback):
    order_id = int(callback.data.split(":")[1])

    success = cancel_order(
        order_id=order_id,
        user_id=callback.from_user.id,
    )

    if not success:
        await callback.answer(
            "❌ Заказ уже нельзя отменить.",
            show_alert=True,
        )
        return

    await callback.answer("Заказ отменён!")

    await callback.message.edit_text(
        callback.message.text
        + "\n\n❌ ЗАКАЗ ОТМЕНЁН"
    )

@dp.callback_query(lambda callback: callback.data.startswith("status:"))
async def change_status(callback):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "⛔ Нет доступа.",
            show_alert=True,
        )
        return

    _, status, order_id = callback.data.split(":")

    order_id = int(order_id)

    order = get_order(order_id)

    if not order:
        await callback.answer(
            "❌ Заказ не найден.",
            show_alert=True,
        )
        return

    _, user_id, product, quantity, old_status = order

    update_order_status(
        order_id=order_id,
        status=status,
    )

    status_names = {
        "processing": "🟡 В работе",
        "completed": "🟢 Завершён",
    }

    status_text = status_names.get(
        status,
        status,
    )

    await callback.answer("Статус обновлён!")

    await callback.message.edit_text(
        f"📦 Заказ #{order_id}\n\n"
        f"Товар: {product}\n"
        f"Количество: {quantity}\n"
        f"Статус: {status_text}"
    )

    await callback.bot.send_message(
        user_id,
        f"🔔 Обновление заказа #{order_id}\n\n"
        f"Товар: {product}\n"
        f"Количество: {quantity}\n\n"
        f"Новый статус: {status_text}",
    )
# Неизвестные сообщения
@dp.message(Command("stats"))
async def statistics_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(
            "⛔ У тебя нет доступа."
        )
        return

    (
        total_orders,
        new_orders,
        processing_orders,
        completed_orders,
        cancelled_orders,
        revenue,
    ) = get_statistics()

    await message.answer(
        "📊 СТАТИСТИКА\n\n"
        f"📦 Всего заказов: {total_orders}\n\n"
        f"🆕 Новых: {new_orders}\n"
        f"🟡 В работе: {processing_orders}\n"
        f"🟢 Завершено: {completed_orders}\n"
        f"❌ Отменено: {cancelled_orders}\n\n"
        f"💰 Выручка: {revenue:.2f} грн"
    )
@dp.message()
async def unknown_message(message: Message):
    await message.answer(
        "Я пока не знаю, что с этим делать 😅\n"
        "Используй кнопки меню."
    )


async def main():
    init_db()

    bot = Bot(token=TOKEN)

    print("🚀 Бот запущен!")
    print("Жду сообщения...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())