import bson
from bson import ObjectId
from flask import url_for
from cleantext import clean

from . import util
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from bot.database import categories as cat, db_client
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, CallbackQueryHandler,
)

from bot.database import places
from bot import env_variables, app
from bot.fs import fs

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

MAIN, SEARCHING, NEXT_OR_EXIT, CHOOSING_CATEGORY = range(4)

main_keyboard = ReplyKeyboardMarkup([
    ["Популярные✨", "Поиск🔎"],
    ["Категории🗃️", "Случайное место🎲"],
], one_time_keyboard=False, resize_keyboard=True)

searching_keyboard = ReplyKeyboardMarkup([
    ["Назад в главное меню◀️"],
], one_time_keyboard=False, input_field_placeholder="Название места", resize_keyboard=True)


welcome_string = "Здесь вы можете узнать о достопримечательностях Удмуртии"
back_string = "Назад в главное меню◀️"
back_string_simplified = clean(back_string, lower=True, no_emoji=True)


async def send_place(update: Update, context: ContextTypes.DEFAULT_TYPE, reply_markup):
    info = context.user_data["results"][context.user_data["results_counter"]]
    with app.app_context():
        if "tg_file_ids" in info:
            for p in info["tg_file_ids"]:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=p,
                )
        else:
            for p in info["photos"]:
                if p['filename']:
                    f = fs.get_last_version(p['filename'])
                    message = await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=f.read(),
                    )
                    file_id = message.photo[-1].file_id
                    places.collect.update_one(
                        {'_id': info["_id"]},
                        {
                            '$push': {'tg_file_ids': file_id}
                        },
                        upsert=True
                    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{info["name"]}\n{info["description"]}",
        reply_markup=reply_markup,
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Оценить место",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"Лайк👍{info["likes"]}", callback_data=f"like {info["_id"]} {update.effective_chat.id}"),
            InlineKeyboardButton(f"Дизлайк👎{info["dislikes"]}", callback_data=f"dislike {info["_id"]} {update.effective_chat.id}"),
        ], [
            InlineKeyboardButton(f"Посмотреть отзывы",
                                 callback_data=f"reviews {info["_id"]} {update.effective_chat.id}")
        ] if "reviews" in info and info["reviews"] else []]),
    )


async def send_review(update: Update, context: ContextTypes.DEFAULT_TYPE, reply_markup):
    info = context.user_data["results"][context.user_data["results_counter"]]
    text = info["text"]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup,
    )


async def edit_message_with_place(update: Update, context: ContextTypes.DEFAULT_TYPE, place_id):
    info = places.collect.find_one({"_id": ObjectId(place_id)})
    query = update.callback_query
    await context.bot.edit_message_reply_markup(
       chat_id=query.message.chat.id,
       message_id=query.message.message_id,
       reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"Лайк👍{info["likes"]}", callback_data=f"like {info["_id"]} {update.effective_chat.id}"),
            InlineKeyboardButton(f"Дизлайк👎{info["dislikes"]}", callback_data=f"dislike {info["_id"]} {update.effective_chat.id}")
        ], [
            InlineKeyboardButton(f"Посмотреть отзывы",
                                 callback_data=f"reviews {info["_id"]} {update.effective_chat.id}")
        ] if "reviews" in info and info["reviews"] else []]))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        welcome_string,
        reply_markup=main_keyboard,
    )
    db_client[env_variables.db_name]["tg_users"].update_one(
        {"chat_id": update.effective_chat.id},
        {"$setOnInsert": {"chat_id": update.effective_chat.id}},
        True
    )

    return MAIN


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if util.compare_input(update.message.text, "поиск"):
        await update.message.reply_text("Введите название места", reply_markup=searching_keyboard)
        return SEARCHING
    if util.compare_input(update.message.text, "категории"):
        categories = cat.get_all()
        keyboard = [[InlineKeyboardButton(c["name"], callback_data=f"category {c["_id"]}")] for c in categories]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)
        return MAIN
    if util.compare_input(update.message.text, "случайное место"):
        context.user_data["function"] = send_place
        context.user_data["results"] = list(places.get_with_photos({"$sample": {"size": 10}}))
        context.user_data["results_counter"] = 0
        return await return_to_main_or_next(update, context, "Следующее случайное место🔽")
    if util.compare_input(update.message.text, "популярные"):
        context.user_data["function"] = send_place
        context.user_data["results"] = list(places.get_with_photos({"$sort": {"likes": -1}}))
        context.user_data["results_counter"] = 0
        return await return_to_main_or_next(update, context, "Следующее популярное место🔽")
    return MAIN


async def searching(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if util.compare_input(update.message.text, back_string_simplified):
        await update.message.reply_text(welcome_string, reply_markup=main_keyboard)
        return MAIN
    context.user_data["function"] = send_place
    context.user_data["results"] = list(places.get_with_photos({"$match": {"$text": {"$search": update.message.text}}}))
    context.user_data["results_counter"] = 0
    return await return_to_main_or_next(update, context, "Следующее найденное место🔽")


async def return_to_main_or_next(update: Update, context: ContextTypes.DEFAULT_TYPE, next_string):
    if not context.user_data["results"]:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Ничего не нашлось", reply_markup=main_keyboard)
        return MAIN
    if len(context.user_data["results"]) == 1:
        await context.user_data["function"](update, context, main_keyboard)
        return MAIN
    next_or_exit_keyboard = ReplyKeyboardMarkup([
        [back_string, next_string],
    ], one_time_keyboard=False, resize_keyboard=True)
    await context.user_data["function"](update, context, next_or_exit_keyboard)
    context.user_data["results_counter"] += 1
    context.user_data["next_string"] = next_string
    return NEXT_OR_EXIT


async def next_or_exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if util.compare_input(update.message.text, back_string_simplified):
        await update.message.reply_text(welcome_string, reply_markup=main_keyboard)
        return MAIN
    if util.compare_input(update.message.text, context.user_data["next_string"]):
        if context.user_data["results_counter"] >= len(context.user_data["results"]) - 1:
            await context.user_data["function"](update, context, main_keyboard)
            return MAIN
        next_or_exit_keyboard = ReplyKeyboardMarkup([
            [back_string, context.user_data["next_string"]],
        ], one_time_keyboard=False, resize_keyboard=True)
        await context.user_data["function"](update, context, next_or_exit_keyboard)
        context.user_data["results_counter"] += 1
        return NEXT_OR_EXIT


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data.split()
    if data[0] == "category":
        return await show_in_category(update, context, data)
    elif data[0] == "like":
        places.give_like(data[1], data[2])
        await edit_message_with_place(update, context, data[1])
    elif data[0] == "dislike":
        places.give_dislike(data[1], data[2])
        await edit_message_with_place(update, context, data[1])
    elif data[0] == "reviews":
        return await show_reviews(update, context, data)


async def show_in_category(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    category_id = data[1]
    category = cat.get_by_id(category_id)
    #next_or_exit_keyboard = ReplyKeyboardMarkup([
    #    ["Назад в главное меню◀️", "Следующая категория🔽"],
    #], one_time_keyboard=False, resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Места категории {category['name']}:") # reply_markup=next_or_exit_keyboard
    res = list(places.get_with_photos(
        {"$match": {
            "category_id": bson.ObjectId(category_id),
        }},
    ))
    context.user_data["function"] = send_place
    context.user_data["results"] = res
    context.user_data["results_counter"] = 0
    return await return_to_main_or_next(update, context, "Следующая категория🔽")


async def show_reviews(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    place_id = data[1]
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Отзывы:")  # reply_markup=next_or_exit_keyboard
    res = places.get_by_id(place_id)["reviews"]
    context.user_data["function"] = send_review
    context.user_data["results"] = res
    context.user_data["results_counter"] = 0
    return await return_to_main_or_next(update, context, "Следующий отзыв🔽")


def configure_application() -> Application:
    application = (Application.builder()
                   .token(env_variables.bot_token)
                   .read_timeout(100)
                   .write_timeout(100)
                   .build())

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN: [
                MessageHandler(
                    filters.ALL, main_menu
                ),
                CallbackQueryHandler(button_handler)
            ],
            SEARCHING: [
                MessageHandler(
                    filters.ALL, searching
                ),
                CallbackQueryHandler(button_handler)
            ],
            NEXT_OR_EXIT: [
                MessageHandler(
                    filters.ALL,
                    next_or_exit,
                ),
                CallbackQueryHandler(button_handler)
            ],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('start', start))
    return application
