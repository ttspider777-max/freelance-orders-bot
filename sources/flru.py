import html
import re
import xml.etree.ElementTree as ET

import httpx

NAME = "FL.ru"
URL = "https://www.fl.ru/rss/all.xml?category=5"  # 5 = Программирование
HEADERS = {"User-Agent": "Mozilla/5.0"}


async def fetch(client: httpx.AsyncClient) -> list[dict]:
    r = await client.get(URL, headers=HEADERS)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    out = []
    for it in root.iter("item"):
        title = html.unescape(it.findtext("title") or "")
        link = it.findtext("link") or ""
        desc = html.unescape(it.findtext("description") or "")
        m = re.search(r"\(Бюджет:\s*([\d\s\xa0]+)", title)
        digits = re.sub(r"\D", "", m.group(1)) if m else ""
        budget_num = int(digits) if digits else 0
        pid = re.search(r"/projects/(\d+)", link)
        out.append({
            "key": f"flru:{pid.group(1) if pid else link}",
            "title": re.sub(r"\s*\(Бюджет:.*?\)\s*$", "", title),
            "description": desc,
            "url": link,
            "budget": f"{budget_num:,} ₽".replace(",", " ") if budget_num else "не указан",
            "budget_num": budget_num,
            "source": NAME,
        })
    return out
