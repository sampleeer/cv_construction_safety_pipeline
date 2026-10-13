# HelmetWatch — контроль касок на стройке

Python-проект для детекции касок и голов без касок на изображениях и видеопотоках.
Подтверждённые нарушения сохраняются в SQLite со снимком, камерой, временем и версией
модели. Страница в браузере показывает детекции на фото и журнал событий.

## Архитектура

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

## Качество кода и CI/CD

PR запускает проверки Python, правил событий, SQLite, преобразования данных, ONNX и API
без скачивания датасета. Push/manual запускает обучение демо, оценку, экспорт, benchmark
и контейнерные smoke-тесты. Tagged release публикует образ только для `qualified` модели.
Настройка DVC remote остаётся задачей окружения; без remote данные скачиваются, а модель
воспроизводится заново. Jenkins-примеры включены в `ci/` и `cd/`.

## Статус модели

Демонстрационный профиль имеет статус **experimental**. Демо обучается на части публичного датасета;
это не подтверждение качества на вашей стройплощадке. Результаты вашего запуска появятся в
`reports/helmet-quality.json`. Пример ранее выполненного эксперимента и проверок
сохранён в [отчёте](docs/verification.md).
Модельные метрики на фотографиях не заменяют оценку событий на реальном видео.

Источник данных и лицензия: [Construction-PPE / AGPL-3.0](https://docs.ultralytics.com/datasets/detect/construction-ppe/).
Исходные веса и экспорт: [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/).
Датасет и веса в Git не включаются; загрузчик и fingerprints позволяют восстановить окружение.

Старое упражнение CelebA сохранено отдельно: `src/api/legacy.py`, `src/data`, `src/models`.
[Формулировка для резюме](docs/resume.md).

## Установка и запуск

### Требования

- Python 3.11 или 3.12 и Git.
- Интернет для установки зависимостей, скачивания датасета и исходных весов.
- Docker с Compose v2, если планируется запуск в контейнере.

Команды ниже приведены для Linux/macOS и выполняются из корня проекта.
Обученные веса, датасет и виртуальное окружение не включены в репозиторий:
при первом запуске их нужно подготовить по инструкции.

### 1. Скачать проект

```bash
git clone https://github.com/sampleeer/cv_construction_safety_pipeline.git
cd cv_construction_safety_pipeline
```

Можно также выбрать **Code → Download ZIP** на странице репозитория и распаковать
архив. В этом случае перейдите в распакованную папку, содержащую `README.md`, и
инициализируйте Git, необходимый для работы DVC:

```bash
git init
```

Для клонированного репозитория этот шаг не нужен.

### 2. Установить зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-export.txt
```

На Windows виртуальное окружение можно создать командой `py -3.11 -m venv .venv`,
а активировать в PowerShell командой `.\.venv\Scripts\Activate.ps1`.

Если нужно только запустить автоматические тесты, достаточно установить
`requirements-dev.txt` вместо `requirements-export.txt` и перейти к разделу
«6. Запустить проверки кода». Датасет и обучение для этих тестов не требуются.

### 3. Подготовить данные и обучить модель

```bash
python scripts/download_model.py
python -m src.helmet.download
cp configs/helmet-demo.yaml params.yaml
dvc repro
```

Пайплайн последовательно выполняет подготовку данных, дообучение YOLO11n,
оценку на test, экспорт в ONNX и benchmark. Демо-профиль использует 384 изображения
для обучения, по 96 для validation/test, 24 эпохи и вход 320×320. По умолчанию
обучение выполняется на CPU; продолжительность зависит от оборудования.

После успешного выполнения появятся:

- `models/helmet-training/best.pt` — обученные веса;
- `models/cv/detector.onnx` и `models/cv/manifest.json` — артефакты для запуска API;
- `reports/helmet-quality.json` — оценка качества;
- `reports/cv-benchmark.json` — результаты измерения производительности.

Для полного обучения используйте другой профиль:

```bash
cp configs/helmet-full.yaml params.yaml
dvc repro
```

В `params.yaml` можно явно указать `device: 0` для NVIDIA GPU или `device: mps`
для поддерживаемого Apple GPU. Полный профиль использует весь набор, 40 эпох,
640×640 и quality gate. На CPU это существенно дольше демо.
Профили являются стартовыми конфигурациями, а не обещанием заданного качества.
Если gate не пройден, экспорт новой модели останавливается. Перед развёртыванием
проверьте версию и статус выбранного артефакта в `models/cv/manifest.json`.

### 4. Запустить приложение

После подготовки модели запустите API в активированном виртуальном окружении:

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

Сервер остаётся запущенным в этом терминале. Откройте в браузере адрес,
который Uvicorn выведет при старте: главная страница содержит проверку фотографии
и журнал нарушений. Добавьте `/docs` к этому адресу, чтобы открыть документацию API.
Для остановки нажмите `Ctrl+C`.

В другом терминале перейдите в корень проекта и активируйте то же окружение.
Задайте адрес своего запущенного API; замените `АДРЕС_СЕРВЕРА` и `ПОРТ` реальными значениями:

```bash
source .venv/bin/activate
export HELMETWATCH_URL="http://АДРЕС_СЕРВЕРА:ПОРТ"
```

При запуске клиента на той же машине используйте адрес из вывода Uvicorn.
Привязка `127.0.0.1` допускает подключения только с машины, на которой запущен сервер.

```bash
# Проверка доступности API и основных endpoints
python scripts/smoke_cv.py --url "$HELMETWATCH_URL"

# Одиночное фото: только детекции, без события
python scripts/demo_cv.py --url "$HELMETWATCH_URL" --image photo.jpg --output artifacts/helmet-detection.jpg

# Видеопоток: подтверждение нарушений, снимки и журнал
python -m src.cv.video --url "$HELMETWATCH_URL" --source video.mp4 --camera site-1 --inspect

# Камера 0, ограниченный запуск
python -m src.cv.video --url "$HELMETWATCH_URL" --source 0 --camera webcam-1 --inspect --max-frames 100
```

Замените `photo.jpg` и `video.mp4` путями к своим файлам. Результат проверки фото
сохранится в `artifacts/helmet-detection.jpg`, результаты обработки видео — в
`reports/video.jsonl`. Подтверждённые события и снимки доступны через веб-страницу.

### Альтернативный запуск через Docker

После выполнения шагов 1–3 приложение можно поднять в контейнере вместо отдельного
процесса Uvicorn. Docker использует подготовленную папку `models/cv`; скачивание
данных и обучение при сборке или старте контейнера не выполняются.
PyTorch в runtime-контейнере отсутствует.

```bash
docker compose up --build -d api
docker compose ps
```

Для просмотра логов используйте `docker compose logs -f api`.
Проверить запущенное приложение можно командой:

```bash
docker compose up --abort-on-container-exit --exit-code-from cd-tests cd-tests
```

Завершить работу и удалить контейнеры приложения:

```bash
docker compose down
```

Volume `helmet-events` сохраняет SQLite и снимки между перезапусками контейнера.
`API_PORT=8001` меняет внешний порт. `ORT_THREADS` и `MAX_INFLIGHT` управляют нагрузкой.
Порт по умолчанию публикуется на интерфейсе `127.0.0.1` машины размещения.
Используйте этот адрес и выбранный `API_PORT` для браузера и `HELMETWATCH_URL`.
`Ctrl+C` завершает просмотр логов; для остановки приложения выполните `docker compose down`.

### 5. Проверить на встроенном примере

После обучения можно подготовить пример без собственных фото и видео.
API должен быть запущен, а `HELMETWATCH_URL` — задан в текущем терминале:

```bash
python -m src.helmet.demo
python scripts/demo_cv.py --url "$HELMETWATCH_URL" --image artifacts/helmet-sample.jpg --output artifacts/helmet-detection.jpg
python -m src.cv.video --url "$HELMETWATCH_URL" --source artifacts/helmet-demo.avi --camera helmet-demo --inspect
```

Демо выбирает успешный пример из validation и повторяет фотографию в видео.
Оно проверяет цепочку обработки и события; это не оценка качества на настоящем видеопотоке.

### 6. Запустить проверки кода

```bash
make lint typecheck test
# Если make недоступен:
ruff check src/cv src/helmet src/api/main.py tests/cv tests/helmet scripts/download_model.py scripts/smoke_cv.py scripts/demo_cv.py
mypy src/helmet/events.py src/helmet/store.py src/helmet/dataset.py src/helmet/quality.py src/cv/detector.py src/cv/video.py src/cv/benchmark.py src/api/main.py
pytest
# Подробный HTML-отчёт покрытия
pytest --cov-report=html:reports/coverage
```

Отчёт можно открыть из файла `reports/coverage/index.html`; непокрытые строки
показаны на страницах отдельных модулей.
