# HelmetWatch — контроль касок на стройке

Python-проект для детекции касок и голов без касок на изображениях и видеопотоках.
Подтверждённые нарушения сохраняются в SQLite со снимком, камерой, временем и версией
модели. Страница в браузере показывает детекции на фото и журнал событий.

```text
Construction-PPE → подготовка 3 классов → дообучение YOLO11n → test evaluation
                                                                   ↓
                                              ONNX export + parity + manifest
                                                                   ↓
Видео → OpenCV → очередь последнего кадра → HTTP /inspect → ONNX Runtime
                                                                   ↓
                                       IoU-треки → подтверждение → SQLite + снимок
                                                                   ↓
                                                   веб-страница /events /metrics
```

## Запуск уже подготовленного проекта

В этой рабочей копии виртуальное окружение и обученная экспериментальная модель подготовлены:

```bash
source .venv/bin/activate
uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

Откройте **http://localhost:8000**: проверка фотографии и журнал нарушений.
Документация API: http://localhost:8000/docs.

```bash
# Одиночное фото: только детекции, без события
python scripts/demo_cv.py --image photo.jpg --output artifacts/helmet-detection.jpg
# Видеопоток: подтверждение нарушений, снимки и журнал
python -m src.cv.video --source video.mp4 --camera site-1 --inspect
# Камера 0, ограниченный запуск
python -m src.cv.video --source 0 --camera webcam-1 --inspect --max-frames 100
```

## Встроенная демонстрация

```bash
python -m src.helmet.demo
python scripts/demo_cv.py --image artifacts/helmet-sample.jpg --output artifacts/helmet-detection.jpg
python -m src.cv.video --source artifacts/helmet-demo.avi --camera helmet-demo --inspect
```

Демо выбирает успешный пример из validation и повторяет фотографию в видео. Оно проверяет
цепочку обработки и события; это не оценка качества на настоящем видеопотоке.

## Воспроизвести с чистого клона

Python 3.11/3.12. Для первого скачивания нужен интернет; обучение идёт локально.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-export.txt
python scripts/download_model.py
python -m src.helmet.download
# prepare → train → evaluate → export → benchmark
# Демо: 384 train, 96 val, 96 test, 24 эпохи, вход 320×320, CPU.
dvc repro
uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

Для полного обучения:

```bash
cp configs/helmet-full.yaml params.yaml
# В params.yaml можно явно указать device: 0 для NVIDIA GPU или device: mps для Apple GPU.
dvc repro
```

Полный профиль: весь набор, 40 эпох, 640×640, quality gate. На CPU это существенно
дольше демо. Профили являются стартовыми конфигурациями, а не обещанием заданного качества.
Если gate не пройден, экспорт новой модели останавливается. Перед развёртыванием проверьте
версию и статус выбранного артефакта в `models/cv/manifest.json`.

## Правила нарушения

Событие создаётся после **трёх последовательных детекций `no_helmet` за минимум секунду**.
Одна плохая детекция или отсутствие каски в списке объектов не создают событие.
Система закрывает событие после двух детекций каски, потери трека или завершения потока;
причина сохраняется отдельно. IoU-трекер работает с областями головы и не распознаёт личности.

[Семантика разметки, архитектура, ограничения и вопросы для интервью](docs/helmet-design.md).

## API

- `POST /detect`: JPEG/PNG байты → боксы, классы, уверенность, время инференса.
- `POST /inspect?camera_id=site-1&frame_id=0`: детекции + треки + переходы событий.
- `POST /cameras/site-1/end`: завершить сессию камеры и закрыть её события.
- `GET /events?camera_id=site-1&limit=50&offset=0`: журнал событий.
- `GET /events/{id}/snapshot`: снимок подтверждённого нарушения.
- `GET /model`: классы, версия, provenance, качество, статус выпуска.
- `GET /health`, `/ready`: liveness и проверка загруженной модели.
- `GET /metrics`: запросы, задержка, число подтверждённых нарушений.

Изображения ограничены 8 MiB / 12 мегапикселями. Максимум два одновременных запроса;
перегрузка возвращает 429. На каждую камеру нужен возрастающий `frame_id`; повторный
кадр возвращает 409. При новом запуске клиента завершите старую сессию либо задайте новый ID.
Сервер запускается **с одним worker**, поскольку треки находятся в памяти процесса.

## Docker

Сначала выполните пайплайн и подготовьте `models/cv`. PyTorch в runtime-контейнере отсутствует.

```bash
docker compose up --build api
# Проверка API из другого терминала
docker compose up --abort-on-container-exit --exit-code-from cd-tests cd-tests
docker compose down
```

Volume `helmet-events` сохраняет SQLite и снимки между перезапусками контейнера.
`API_PORT=8001` меняет внешний порт. `ORT_THREADS` и `MAX_INFLIGHT` управляют нагрузкой.
Порты по умолчанию доступны с localhost.

## Качество кода и CI/CD

```bash
make lint typecheck test
# Если make недоступен:
ruff check src/cv src/helmet src/api/main.py tests/cv tests/helmet scripts/download_model.py scripts/smoke_cv.py scripts/demo_cv.py
mypy src/helmet/events.py src/helmet/store.py src/helmet/dataset.py src/cv/detector.py src/cv/video.py src/cv/benchmark.py src/api/main.py
pytest
```

PR запускает проверки Python, правил событий, SQLite, преобразования данных, ONNX и API
без скачивания датасета. Push/manual запускает обучение демо, оценку, экспорт, benchmark
и контейнерные smoke-тесты. Tagged release публикует образ только для `qualified` модели.
Настройка DVC remote остаётся задачей окружения; без remote данные скачиваются, а модель
воспроизводится заново. Jenkins-примеры включены в `ci/` и `cd/`.

## Статус модели

Локальный результат — **experimental**. Демо обучается на части публичного датасета;
это не подтверждение качества на вашей стройплощадке. Точные результаты находятся в
`reports/helmet-quality.json`, детали выполненных проверок — в [отчёте](docs/verification.md).
Модельные метрики на фотографиях не заменяют оценку событий на реальном видео.

Источник данных и лицензия: [Construction-PPE / AGPL-3.0](https://docs.ultralytics.com/datasets/detect/construction-ppe/).
Исходные веса и экспорт: [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/).
Датасет и веса в Git не включаются; загрузчик и fingerprints позволяют восстановить окружение.

Старое упражнение CelebA сохранено отдельно: `src/api/legacy.py`, `src/data`, `src/models`.
[Формулировка для резюме](docs/resume.md).
