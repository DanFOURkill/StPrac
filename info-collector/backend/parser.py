"""Модуль загрузки и разбора HTML-страниц."""

from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup


def collect_information(url: str, query: str) -> dict[str, Any]:
    """Загружает страницу, извлекает заголовок, абзацы и ссылки.

    Текстовые фрагменты фильтруются по поисковому запросу без учёта регистра.
    Если запрос пустой, возвращаются все найденные абзацы.
    """

    response = requests.get(url, timeout=10, headers={"User-Agent": "InfoCollector/1.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else "Без заголовка"

    paragraphs = [paragraph.get_text(" ", strip=True) for paragraph in soup.find_all("p")]
    paragraphs = [text for text in paragraphs if text]

    normalized_query = query.strip().lower()
    if normalized_query:
        fragments = [text for text in paragraphs if normalized_query in text.lower()]
    else:
        fragments = paragraphs

    links = [link.get("href") for link in soup.find_all("a", href=True)]

    return {
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "query": query.strip(),
        "url": url,
        "title": title,
        "fragments": fragments,
        "links_count": len(links),
    }
