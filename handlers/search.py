import os
import urllib.parse
import logging
from aiohttp import ClientSession
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import search_books, get_book_by_id, increment_downloads, log_download, get_stats
from keyboards import books_list_keyboard, book_keyboard, main_menu, cancel_keyboard, dbooks_recent_books_list, dbooks_book_keyboard

router = Router()

class SearchState(StatesGroup):
    waiting_query = State()

@router.message(F.text == "🔍 Kitob qidirish")
async def search_start(message: Message, state: FSMContext):
    # Dbooks.org also has books, so we should always allow search.
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

    # First, try to search in the local database
    books = search_books(query)
    await state.clear()

    if books:
        await message.answer(
            f"✅ <b>{len(books)} ta kitob topildi:</b>",
            parse_mode="HTML",
            reply_markup=books_list_keyboard(books, back_callback="back_main")
        )
        return

    # If local database has no books, fall back to dbooks.org API
    fetching_msg = await message.answer("⏳ Lokal bazadan topilmadi, global bazadan qidirilmoqda...", reply_markup=main_menu())

    async with ClientSession() as session:
        try:
            resp = await session.get(f"https://www.dbooks.org/api/search/{urllib.parse.quote(query)}")
            data = await resp.json()

            if data.get("status") == "ok":
                d_books = (data.get("books") or [])[:20]

                text = "🌐 <b>Global natijalar: {}</b>\n\n{}".format(
                    len(d_books),
                    "\n\n".join(
                        f"<b>{i + 1}.</b> {b.get('title', '')} — <i>{b.get('authors', '')}</i>"
                        for i, b in enumerate(d_books)
                    )
                )

                await message.answer(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=dbooks_recent_books_list(d_books)
                )
            else:
                await message.answer(
                    f"😔 <b>«{query}»</b> bo'yicha hech narsa topilmadi.\n\nBoshqa so'z bilan urinib ko'ring.",
                    parse_mode="HTML"
                )
        except Exception as e:
            logging.exception(e)
            await message.answer("Qidiruv jarayonida xatolik yuz berdi.")
        finally:
            try:
                await fetching_msg.delete()
            except Exception:
                pass

# LOCAL BOOK DETAILS
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

# LOCAL BOOK DOWNLOAD
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

# DBOOKS DETAILS
@router.callback_query(F.data.startswith("dbook_id_"))
async def dbook_details(call: CallbackQuery):
    await call.message.delete()
    book_id = call.data.split("_", 2)[2]

    async with ClientSession() as session:
        try:
            resp = await session.get(f"https://www.dbooks.org/api/book/{book_id}")
            data = await resp.json()

            if data.get("status") != "ok":
                await call.message.answer("❌ Kitob topilmadi.")
                await call.answer()
                return

            caption = (
                f"<b>Sarlavha:</b> {data.get('title', '')}\n\n"
                f"<b>Tavsif:</b> {data.get('description', '')}\n\n"
                f"<b>Muallif:</b> <i>{data.get('authors', '')}</i>\n\n"
                f"<b>Nashriyot:</b> {data.get('publisher', '')}\n"
                f"<b>Sahifalar:</b> {data.get('pages', '')}\n"
                f"<b>Yil:</b> {data.get('year', '')}"
            )

            await call.message.answer_photo(
                photo=data.get("image"),
                caption=caption,
                parse_mode="HTML",
                reply_markup=dbooks_book_keyboard(
                    url=data.get("url"),
                    book_id=book_id
                )
            )
            await call.answer()
        except Exception as e:
            logging.exception(e)
            await call.answer("Kitobni yuklashda xatolik yuz berdi.", show_alert=True)

# DBOOKS DOWNLOAD
@router.callback_query(F.data.startswith("dbook_down_"))
async def dbook_download(call: CallbackQuery):
    book_id = call.data.split("_", 2)[2]
    await call.answer("Fayl tayyorlanmoqda...")
    fetching_msg = await call.message.answer("⏳ Yuklab olinmoqda, kuting...")
    file_path = None

    async with ClientSession() as session:
        try:
            info_resp = await session.get(f"https://www.dbooks.org/api/book/{book_id}")
            info = await info_resp.json()

            if info.get("status") != "ok":
                await fetching_msg.edit_text("❌ Kitob topilmadi.")
                return

            file_url = info.get("download")
            if not file_url:
                await fetching_msg.edit_text("❌ Yuklab olish havolasi mavjud emas.")
                return

            safe_title = (info.get("title") or f"book_{book_id}").replace("/", "_")
            file_path = f"/tmp/{safe_title}_{book_id}.pdf"

            dl_resp = await session.get(file_url)
            if dl_resp.status != 200:
                await fetching_msg.edit_text("❌ Yuklab olish amalga oshmadi.")
                return

            with open(file_path, "wb") as f:
                async for chunk in dl_resp.content.iter_chunked(1024 * 64):
                    f.write(chunk)

            await call.message.answer_document(
                document=FSInputFile(file_path),
                caption="📘 Kitobingiz tayyor."
            )
        except Exception as e:
            logging.exception(e)
            try:
                await fetching_msg.edit_text("❌ Kutilmagan xato yuz berdi.")
            except Exception:
                pass
        finally:
            try:
                await fetching_msg.delete()
            except Exception:
                pass
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
