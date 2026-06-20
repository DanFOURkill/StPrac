"""Backend FastAPI для учебного проекта InfoCollector."""

import csv
import io

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .database import delete_result, get_history, get_result, init_db, save_result
from .models import CollectRequest
from .parser import collect_information

app = FastAPI(title="InfoCollector API", description="Сбор информации с веб-страниц")

# Разрешаем frontend-странице обращаться к API во время локального запуска.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Инициализирует базу данных при запуске приложения."""

    init_db()


@app.get("/")
def root() -> dict[str, str]:
    """Проверочный маршрут API."""

    return {"message": "InfoCollector API работает"}


@app.post("/collect")
def collect(request: CollectRequest) -> dict:
    """Принимает URL и запрос, собирает данные и сохраняет результат."""

    try:
        result = collect_information(str(request.url), request.query)
    except requests.RequestException as error:
        raise HTTPException(status_code=400, detail=f"Не удалось загрузить страницу: {error}") from error

    result["id"] = save_result(result)
    return result


@app.get("/history")
def history() -> list[dict]:
    """Возвращает историю всех запросов."""

    return get_history()


@app.get("/results/{result_id}")
def result(result_id: int) -> dict:
    """Возвращает сохранённый результат по ID."""

    saved_result = get_result(result_id)
    if saved_result is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return saved_result


@app.delete("/results/{result_id}")
def delete(result_id: int) -> dict[str, str]:
    """Удаляет запись из истории."""

    if not delete_result(result_id):
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return {"message": "Запись удалена"}


@app.get("/export")
def export_csv() -> StreamingResponse:
    """Экспортирует историю запросов в CSV-файл."""

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "collected_at", "query", "url", "title", "fragments", "links_count"])

    for item in get_history():
        writer.writerow(
            [
                item["id"],
                item["collected_at"],
                item["query"],
                item["url"],
                item["title"],
                " | ".join(item["fragments"]),
                item["links_count"],
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=info_collector_results.csv"},
    )
