import json

import httpx

NAME = "Kwork"
URL = "https://kwork.ru/projects?c=all"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}


async def fetch(client: httpx.AsyncClient) -> list[dict]:
    r = await client.get(URL, headers=HEADERS)
    r.raise_for_status()
    t = r.text
    i = t.find("stateData=")
    if i < 0:
        return []
    data, _ = json.JSONDecoder().raw_decode(t[i + len("stateData="):])
    wants = (data.get("wantsListData") or {}).get("wants") or []
    out = []
    for w in wants:
        price = int(float(w.get("priceLimit") or 0))
        out.append({
            "key": f"kwork:{w['id']}",
            "title": w.get("name", ""),
            "description": w.get("description", ""),
            "url": f"https://kwork.ru/projects/{w['id']}",
            "budget": f"до {price:,} ₽".replace(",", " ") if price else "не указан",
            "budget_num": price,
            "source": NAME,
        })
    return out
