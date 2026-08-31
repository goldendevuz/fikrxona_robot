from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import search_books, get_book_by_id, increment_downloads, log_download, get_stats
from keyboards import books_list_keyboard, book_keyboard, main_menu, cancel_keyboard

router = Router()


class SearchState(StatesGroup):
    waiting_query = State()


@router.message(F.text == "🔍 Kitob qidirish")
async def search_start(message: Message, state: FSMContext):
    books_count, _, _ = get_stats()
    if books_count == 0:
        await message.answer("😔 Hozircha kitoblar yo'q.", reply_markup=main_menu())
        return

    await state.set_state(SearchState.waiting_query)
    await message.answer("🔍 Kitob nomi yoki muallif ismini kiriting:", reply_markup=cancel_keyboard())


@router.message(SearchState.waiting_query)
async def search_process(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=main_menu())
        return

    query = message.text.strip()
    if len(query) < 2:
        await message.answer("⚠️ Kamida 2 ta harf kiriting!")
        return

    books = search_books(query)
    await state.clear()

    if not books:
        await message.answer(
            f"😔 <b>«{query}»</b> bo'yicha hech narsa topilmadi.\n\nBoshqa so'z bilan urinib ko'ring.",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        return

    await message.answer(
        f"✅ <b>{len(books)} ta kitob topildi:</b>",
        parse_mode="HTML",
        reply_markup=books_list_keyboard(books, back_callback="back_main")
    )


@router.callback_query(F.data.startswith("book_"))
async def show_book(callback: CallbackQuery):
    book_id = int(callback.data.split("_")[1])
    book = get_book_by_id(book_id)

    if not book:
        await callback.answer("❌ Kitob topilmadi!", show_alert=True)
        return

    category = book["category_name"] or "Noma'lum"
    description = book["description"] or "Tavsif yo'q"
    text = (
        f"📖 <b>{book['title']}</b>\n\n"
        f"👤 Muallif: <i>{book['author']}</i>\n"
        f"🗂 Kategoriya: {category}\n"
        f"📥 Yuklab olingan: {book['downloads']} marta\n\n"
        f"📝 <b>Tavsif:</b>\n{description}"
    )

    if book["cover_id"]:
        await callback.message.answer_photo(
            photo=book["cover_id"],
            caption=text,
            parse_mode="HTML",
            reply_markup=book_keyboard(book_id)
        )
    else:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=book_keyboard(book_id))

    await callback.answer()


@router.callback_query(F.data.startswith("download_"))
async def download_book(callback: CallbackQuery):
    book_id = int(callback.data.split("_")[1])
    book = get_book_by_id(book_id)

    if not book:
        await callback.answer("❌ Kitob topilmadi!", show_alert=True)
        return

    if not book["file_id"]:
        await callback.answer("⚠️ Bu kitob hali yuklanmagan!", show_alert=True)
        return

    await callback.message.answer_document(
        document=book["file_id"],
        caption=f"📖 <b>{book['title']}</b>\n👤 {book['author']}",
        parse_mode="HTML"
    )

    increment_downloads(book_id)
    log_download(callback.from_user.id, book_id)
    await callback.answer("✅ Yuklab olindi!")
