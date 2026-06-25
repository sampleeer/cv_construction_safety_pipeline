# CelebA Smiling MLOps

## Датасет

Используется CelebA: более 200 000 изображений лиц знаменитостей и 40 бинарных
атрибутов на изображение. Официальная страница:
<http://mmlab.ie.cuhk.edu.hk/projects/CelebA.html>.

Для итогового запуска скачайте `Attributes Annotations` и положите файл:

```bash
data/raw/list_attr_celeba.txt
```

Для CI и локальной проверки без полного датасета включен demo-режим: если файл
отсутствует, pipeline создает небольшой детерминированный CelebA-like набор.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

dvc repro
pytest
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Проверка API:

```bash
curl http://localhost:8000/model
curl -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"features":{"Mouth_Slightly_Open":1,"High_Cheekbones":1,"Young":1,"Attractive":1}}'
```

## Docker

```bash
docker build -t celeba-smiling-api:local .
docker compose up api
```

По умолчанию compose публикует API на `localhost:8001`, чтобы не конфликтовать
с локальным dev-сервером на `8000`. Для публикации на `8000`:

```bash
API_PORT=8000 docker compose up api
```

Функциональные CD-тесты внутри контейнера:

```bash
docker compose up --build --abort-on-container-exit --exit-code-from cd-tests cd-tests
```

## DVC

Pipeline описан в `dvc.yaml`:

1. `prepare` создает `data/processed/celeba_smiling.csv`;
2. `train` обучает `models/model.joblib`;
3. `evaluate` пишет `reports/metrics.json` и проверяет quality gate.

После загрузки официального файла:

```bash
dvc add data/raw/list_attr_celeba.txt
dvc repro
```

## CI/CD

Доступны два варианта конфигурации:

- `ci/Jenkinsfile` - CI: зависимости, DVC pipeline, тесты, сборка Docker image,
  push в DockerHub при pull request в `main`, генерация `dev_sec_ops.yml`;
- `cd/Jenkinsfile` - CD: запуск контейнера и функциональные тесты по
  `scenario.json`;
- `.github/workflows/ci.yml` - аналогичный GitHub Actions workflow для PR и
  ручного запуска.

Для DockerHub нужны секреты/credentials:

- Jenkins credential `dockerhub` с логином и токеном DockerHub;
- GitHub Actions secrets `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN`.

## Структура

```text
src/data/prepare.py       # подготовка CelebA attributes
src/models/train.py       # обучение LogisticRegression
src/models/evaluate.py    # расчет метрик и quality gate
src/api/main.py           # FastAPI сервис
tests/                    # pytest тесты
scripts/run_scenario.py   # CD functional scenario runner
scripts/generate_dev_sec_ops.py
config.ini
dvc.yaml
Dockerfile
docker-compose.yml
scenario.json
```
