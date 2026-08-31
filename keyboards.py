from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="🔍 Kitob qidirish"), KeyboardButton(text="📚 Kategoriyalar"))
    kb.row(KeyboardButton(text="⭐ Top kitoblar"), KeyboardButton(text="🎯 Tavsiya"))
    kb.row(KeyboardButton(text="📥 Yuklab olganlarim"), KeyboardButton(text="ℹ️ Yordam"))
    return kb.as_markup(resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="➕ Kitob qo'shish"), KeyboardButton(text="🗂 Kategoriya qo'shish"))
    kb.row(KeyboardButton(text="🗑 Kitob o'chirish"), KeyboardButton(text="📊 Statistika"))
    kb.row(KeyboardButton(text="🔙 Asosiy menyu"))
    return kb.as_markup(resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text="❌ Bekor qilish"))
    return kb.as_markup(resize_keyboard=True)


def categories_keyboard(categories) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=cat["name"], callback_data=f"cat_{cat['id']}")
    kb.adjust(2)
    return kb.as_markup()


def book_keyboard(book_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📥 Yuklab olish", callback_data=f"download_{book_id}")
    kb.button(text="🔙 Orqaga", callback_data="back_to_search")
    kb.adjust(1)
    return kb.as_markup()


def books_list_keyboard(books, back_callback="back_main") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for book in books:
        kb.button(
            text=f"📖 {book['title']} — {book['author']}",
            callback_data=f"book_{book['id']}"
        )
    kb.button(text="🔙 Orqaga", callback_data=back_callback)
    kb.adjust(1)
    return kb.as_markup()


def admin_delete_keyboard(books) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for book in books:
        kb.button(text=f"🗑 {book['title']}", callback_data=f"del_book_{book['id']}")
    kb.button(text="🔙 Orqaga", callback_data="back_admin")
    kb.adjust(1)
    return kb.as_markup()


def confirm_delete_keyboard(book_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, o'chir", callback_data=f"confirm_del_{book_id}")
    kb.button(text="❌ Yo'q", callback_data="back_admin")
    kb.adjust(2)
    return kb.as_markup()


def admin_delete_cat_keyboard(categories) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=f"🗑 {cat['name']}", callback_data=f"del_cat_{cat['id']}")
    kb.button(text="🔙 Orqaga", callback_data="back_admin")
    kb.adjust(1)
    return kb.as_markup()


def dbooks_recent_books_list(books_data) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for i, book in enumerate(books_data):
        kb.button(text=str(i + 1), callback_data=f"dbook_id_{book['id']}")
    kb.adjust(5)
    return kb.as_markup()


def dbooks_book_keyboard(url: str, book_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="↗️ Havola", url=url)
    kb.button(text="📥 Yuklab olish", callback_data=f"dbook_down_{book_id}")
    kb.button(text="🔙 Orqaga", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()
