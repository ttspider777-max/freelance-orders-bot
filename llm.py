import httpx

import config
import about_me as profile

SYSTEM = f"""Ты помогаешь фрилансеру писать отклики на заказы. Пиши ТОЛЬКО готовый текст отклика, без пояснений.

О фрилансере:
{profile.ABOUT}

Требования к стилю:
{profile.STYLE}"""


async def make_reply(order: dict, hint: str = "") -> str:
    user = (
        f"Заказ с биржи {order['source']}.\nНазвание: {order['title']}\nБюджет: {order['budget']}\n"
        f"Описание: {order['description'][:3000]}\n\nНапиши отклик."
    )
    if hint:
        user += f"\nУчти пожелание: {hint}"
    headers = {"Authorization": f"Bearer {config.LLM_KEY}"} if config.LLM_KEY else {}
    body = {
        "model": config.LLM_MODEL,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
    }
    for _ in range(3):
        try:
            async with httpx.AsyncClient(timeout=90) as c:
                r = await c.post(config.LLM_URL, json=body, headers=headers)
                r.raise_for_status()
                text = (r.json()["choices"][0]["message"]["content"] or "").strip()
                if text:
                    return text
        except Exception:  # noqa: BLE001
            pass
    return _fallback(order)


def _fallback(order: dict) -> str:
    return (
        f"Добрый день! Заинтересовала ваша задача «{order['title']}». Я Full Stack разработчик: "
        f"делаю сайты и Telegram-ботов любой сложности, беру проект от идеи до запуска и поддержки. "
        f"Давайте уточним детали и сроки, чтобы я точно оценил работу. "
        f"Примеры моих работ: {profile.PORTFOLIO}"
    )
