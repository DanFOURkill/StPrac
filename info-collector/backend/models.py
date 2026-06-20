"""Pydantic-модели для API InfoCollector."""

from pydantic import BaseModel, HttpUrl


class CollectRequest(BaseModel):
    """Данные, которые пользователь отправляет из формы."""

    query: str
    url: HttpUrl
