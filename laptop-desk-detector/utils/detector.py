"""Детекция ноутбуков на изображениях и видео с помощью YOLOv8."""

from pathlib import Path
from typing import Dict, List, Tuple

import cv2
from ultralytics import YOLO

# В COCO-классификации YOLO класс laptop имеет индекс 63.
LAPTOP_CLASS_ID = 63
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

_MODEL: YOLO | None = None


def get_model(model_name: str = "yolov8n.pt") -> YOLO:
    """Ленивая загрузка предобученной модели YOLOv8.

    При первом запуске ultralytics автоматически скачает веса, если их нет локально.
    """
    global _MODEL
    if _MODEL is None:
        _MODEL = YOLO(model_name)
    return _MODEL


def is_image(filename: str) -> bool:
    """Проверяет, относится ли файл к поддерживаемым изображениям."""
    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS


def is_video(filename: str) -> bool:
    """Проверяет, относится ли файл к поддерживаемым видео."""
    return Path(filename).suffix.lower() in VIDEO_EXTENSIONS


def _draw_laptop_boxes(frame, detections: List[Dict]) -> None:
    """Рисует рамки и подписи на кадре."""
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        conf = det["confidence"]
        label = f"Ноутбук {conf:.2f}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), (46, 125, 50), 2)
        cv2.rectangle(frame, (x1, max(0, y1 - 28)), (x1 + 170, y1), (46, 125, 50), -1)
        cv2.putText(frame, label, (x1 + 5, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


def detect_frame(frame, confidence_threshold: float) -> Tuple[object, List[Dict]]:
    """Ищет ноутбуки на одном кадре, игнорируя все остальные классы."""
    model = get_model()
    results = model.predict(frame, conf=confidence_threshold, classes=[LAPTOP_CLASS_ID], verbose=False)
    detections: List[Dict] = []

    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            if cls_id != LAPTOP_CLASS_ID or conf < confidence_threshold:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            detections.append({"bbox": [x1, y1, x2, y2], "confidence": round(conf, 4)})

    annotated = frame.copy()
    _draw_laptop_boxes(annotated, detections)
    return annotated, detections


def process_image(input_path: Path, output_path: Path, confidence_threshold: float) -> Dict:
    """Обрабатывает изображение и сохраняет картинку с bounding boxes."""
    image = cv2.imread(str(input_path))
    if image is None:
        raise ValueError("Не удалось прочитать изображение через OpenCV.")

    annotated, detections = detect_frame(image, confidence_threshold)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), annotated)

    return {
        "laptops_count": len(detections),
        "confidences": [d["confidence"] for d in detections],
        "result_path": str(output_path),
    }


def process_video(input_path: Path, output_path: Path, confidence_threshold: float) -> Dict:
    """Обрабатывает видео покадрово и сохраняет результат с рамками."""
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise ValueError("Не удалось открыть видео через OpenCV.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    counts: List[int] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        annotated, detections = detect_frame(frame, confidence_threshold)
        counts.append(len(detections))
        writer.write(annotated)

    cap.release()
    writer.release()

    if not counts:
        raise ValueError("Видео не содержит кадров для обработки.")

    return {
        "avg_laptops_count": round(sum(counts) / len(counts), 2),
        "max_laptops_count": max(counts),
        "frames_processed": len(counts),
        "result_path": str(output_path),
    }
