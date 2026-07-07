"""Генерация Excel- и PDF-отчётов по истории запросов."""

from pathlib import Path
from typing import Dict, List

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def generate_excel(history: List[Dict]) -> Path:
    """Создаёт Excel-файл с полной историей обработок."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "history_report.xlsx"
    df = pd.DataFrame(history)
    if not df.empty:
        df = df.rename(columns={
            "id": "ID", "timestamp": "Дата и время", "filename": "Файл",
            "file_type": "Тип", "laptops_count": "Ноутбуков на изображении",
            "avg_laptops_count": "Среднее по видео", "max_laptops_count": "Максимум в кадре",
            "confidence_threshold": "Confidence", "result_path": "Результат",
            "processing_time_seconds": "Время обработки, сек.",
        })
    df.to_excel(output_path, index=False)
    return output_path


def generate_pdf(history: List[Dict]) -> Path:
    """Создаёт PDF-отчёт с таблицей истории."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "history_report.pdf"
    doc = SimpleDocTemplate(str(output_path), pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = [Paragraph("Отчёт по детекции ноутбуков", styles["Title"]), Spacer(1, 12)]

    data = [["ID", "Дата", "Файл", "Тип", "Кол-во", "Среднее", "Макс.", "Conf", "Время"]]
    for row in history:
        data.append([
            row.get("id"), row.get("timestamp"), row.get("filename"), row.get("file_type"),
            row.get("laptops_count") or "-", row.get("avg_laptops_count") or "-",
            row.get("max_laptops_count") or "-", row.get("confidence_threshold"),
            row.get("processing_time_seconds"),
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f6f46")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    doc.build(elements)
    return output_path
