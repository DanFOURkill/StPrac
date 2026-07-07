"""Flask-приложение для детекции ноутбуков на партах."""

import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from utils.database import add_request, get_history, init_db
from utils.detector import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, is_image, is_video, process_image, process_video
from utils.reports import generate_excel, generate_pdf

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
RESULT_DIR = BASE_DIR / "static" / "results"
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 МБ

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)

init_db()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)


def _relative_static_path(path: Path) -> str:
    """Преобразует абсолютный путь внутри static в URL-путь для браузера."""
    return "/" + str(path.relative_to(BASE_DIR)).replace("\\", "/")


@app.route("/")
def index():
    """Главная страница учебного приложения."""
    return render_template("index.html", history=get_history(limit=10))


@app.route("/process", methods=["POST"])
def process_file():
    """Принимает изображение или видео, запускает YOLOv8 и возвращает JSON."""
    if "file" not in request.files:
        return jsonify({"error": "Файл не загружен."}), 400

    uploaded = request.files["file"]
    if not uploaded.filename:
        return jsonify({"error": "Файл не выбран."}), 400

    try:
        confidence = float(request.form.get("confidence", 0.35))
        confidence = min(max(confidence, 0.01), 0.99)
    except ValueError:
        return jsonify({"error": "Некорректный confidence threshold."}), 400

    filename = secure_filename(uploaded.filename)
    ext = Path(filename).suffix.lower()
    if ext not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
        return jsonify({"error": "Неподдерживаемый формат файла."}), 400

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_name = f"{int(time.time())}_{filename}"
    input_path = UPLOAD_DIR / unique_name
    uploaded.save(input_path)

    start = time.perf_counter()
    try:
        if is_image(filename):
            output_path = RESULT_DIR / f"result_{Path(unique_name).stem}.jpg"
            result = process_image(input_path, output_path, confidence)
            file_type = "image"
            payload = {
                "file_type": file_type,
                "laptops_count": result["laptops_count"],
                "confidences": result["confidences"],
                "result_path": _relative_static_path(output_path),
            }
        elif is_video(filename):
            output_path = RESULT_DIR / f"result_{Path(unique_name).stem}.mp4"
            result = process_video(input_path, output_path, confidence)
            file_type = "video"
            payload = {
                "file_type": file_type,
                "avg_laptops_count": result["avg_laptops_count"],
                "max_laptops_count": result["max_laptops_count"],
                "frames_processed": result["frames_processed"],
                "result_path": _relative_static_path(output_path),
            }
        else:
            return jsonify({"error": "Неподдерживаемый формат файла."}), 400
    except Exception as exc:  # Ошибка чтения файла или модели возвращается пользователю в безопасном виде.
        return jsonify({"error": f"Ошибка обработки или модели: {exc}"}), 500

    processing_time = round(time.perf_counter() - start, 3)
    payload.update({"timestamp": timestamp, "confidence_threshold": confidence, "processing_time_seconds": processing_time})

    record = {
        "timestamp": timestamp,
        "filename": filename,
        "file_type": file_type,
        "laptops_count": payload.get("laptops_count"),
        "avg_laptops_count": payload.get("avg_laptops_count"),
        "max_laptops_count": payload.get("max_laptops_count"),
        "confidence_threshold": confidence,
        "result_path": payload["result_path"],
        "processing_time_seconds": processing_time,
    }
    payload["request_id"] = add_request(record)
    if payload.get("laptops_count") == 0 or payload.get("max_laptops_count") == 0:
        payload["message"] = "Ноутбуки не найдены при выбранном пороге confidence."
    return jsonify(payload)


@app.route("/history")
def history():
    """Возвращает историю запросов в JSON."""
    return jsonify(get_history())


@app.route("/export/excel")
def export_excel():
    """Выгружает историю в Excel."""
    path = generate_excel(get_history())
    return send_file(path, as_attachment=True, download_name="history_report.xlsx")


@app.route("/export/pdf")
def export_pdf():
    """Выгружает историю в PDF."""
    path = generate_pdf(get_history())
    return send_file(path, as_attachment=True, download_name="history_report.pdf")


@app.errorhandler(413)
def too_large(_error):
    """Обработка слишком больших файлов."""
    return jsonify({"error": "Файл слишком большой. Максимальный размер — 100 МБ."}), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
