import asyncio
import html
import logging

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions, Message

import config
import db
import llm
from sources import ALL

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
state = {"paused": False}
NO_PREVIEW = LinkPreviewOptions(is_disabled=True)


def matches(o: dict) -> bool:
    text = f"{o['title']} {o['description']}".lower()
    if any(w in text for w in config.STOP_WORDS):
        return False
    if o.get("budget_num") and o["budget_num"] < config.MIN_BUDGET:
        return False
    return any(w in text for w in config.KEYWORDS)


def kb(o: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Открыть заказ", url=o["url"])],
        [InlineKeyboardButton(text="✍️ Сгенерировать отклик", callback_data=f"gen:{o['key']}")],
    ])


def card(o: dict) -> str:
    desc = html.escape(o["description"].strip())
    if len(desc) > 1500:
        desc = desc[:1500] + "…"
    return f"🆕 <b>{html.escape(o['title'])}</b>\n🏷 {o['source']} · 💰 {html.escape(o['budget'])}\n\n{desc}"


async def send_order(o: dict, with_reply: bool = True) -> None:
    db.save_order(o)
    await bot.send_message(config.OWNER_ID, card(o), reply_markup=kb(o), link_preview_options=NO_PREVIEW)
    if with_reply:
        await send_reply(o)


async def send_reply(o: dict) -> None:
    text = await llm.make_reply(o)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Другой вариант", callback_data=f"gen:{o['key']}")],
        [InlineKeyboardButton(text="🔗 Открыть заказ", url=o["url"])],
    ])
    await bot.send_message(
        config.OWNER_ID,
        f"📝 <b>Отклик (нажми на текст, чтобы скопировать):</b>\n\n<code>{html.escape(text)}</code>",
        reply_markup=markup, link_preview_options=NO_PREVIEW,
    )


async def poll_once(first_run: bool) -> int:
    sent = 0
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for src in ALL:
            try:
                orders = await src.fetch(client)
            except Exception as e:  # noqa: BLE001
                logging.warning("%s: %s", src.NAME, e)
                continue
            for o in reversed(orders):
                if db.is_seen(o["key"]):
                    continue
                db.mark_seen(o["key"])
                if first_run or not matches(o):
                    continue
                await send_order(o)
                sent += 1
                await asyncio.sleep(1)
    return sent


async def poller() -> None:
    first = True  # при первом запуске только запоминаем текущие заказы, чтобы не завалить чат
    while True:
        if not state["paused"]:
            try:
                await poll_once(first)
                first = False
            except Exception:  # noqa: BLE001
                logging.exception("poll failed")
        await asyncio.sleep(config.POLL_INTERVAL)


@dp.message(Command("start"), F.from_user.id == config.OWNER_ID)
async def start(m: Message):
    await m.answer(
        "Бот ищет заказы на Kwork и FL.ru и присылает их с готовым откликом.\n\n"
        "/check — проверить биржи прямо сейчас\n/pause — пауза\n/resume — продолжить\n"
        "/test — прислать последний подходящий заказ"
    )


@dp.message(Command("pause"), F.from_user.id == config.OWNER_ID)
async def pause(m: Message):
    state["paused"] = True
    await m.answer("⏸ Пауза")


@dp.message(Command("resume"), F.from_user.id == config.OWNER_ID)
async def resume(m: Message):
    state["paused"] = False
    await m.answer("▶️ Поиск продолжен")


@dp.message(Command("check"), F.from_user.id == config.OWNER_ID)
async def check(m: Message):
    n = await poll_once(False)
    await m.answer(f"Готово, новых подходящих заказов: {n}")


@dp.message(Command("test"), F.from_user.id == config.OWNER_ID)
async def test(m: Message):
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for src in ALL:
            for o in await src.fetch(client):
                if matches(o):
                    await send_order(o)
                    return
    await m.answer("Подходящих заказов сейчас нет")


@dp.callback_query(F.data.startswith("gen:"), F.from_user.id == config.OWNER_ID)
async def gen(c: CallbackQuery):
    o = db.get_order(c.data[4:])
    if not o:
        await c.answer("Заказ не найден", show_alert=True)
        return
    await c.answer("Генерирую…")
    await send_reply(o)


async def main():
    asyncio.create_task(poller())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
