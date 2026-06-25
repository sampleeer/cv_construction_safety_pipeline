# Отчет о проделанной работе

## Цель

Получить навыки разработки CI/CD pipeline для ML-модели с проверкой метрик
качества, контейнеризацией и функциональным тестированием контейнера.

## Датасет

Выбран CelebA. Согласно официальной странице датасет содержит 202 599
изображений лиц, 10 177 идентичностей, 5 landmark-точек и 40 бинарных атрибутов.
В работе используется файл атрибутов `list_attr_celeba.txt`.

Целевая переменная: `Smiling`.

## Подготовка данных

Скрипт `src/data/prepare.py` читает официальный формат CelebA:

- первая строка - количество объектов;
- вторая строка - имена атрибутов;
- далее строки вида `image_id attr_1 attr_2 ... attr_40`;
- значения `-1` конвертируются в `0`, значения `1` сохраняются как `1`.

Результат сохраняется в `data/processed/celeba_smiling.csv`.

## Модель

Использован классический алгоритм `LogisticRegression` из scikit-learn.
Модель предсказывает бинарный атрибут `Smiling` по остальным атрибутам CelebA.

Гиперпараметры находятся в `config.ini`:

- `C = 1.0`;
- `max_iter = 1000`;
- `class_weight = balanced`;
- `solver = liblinear`.

Метрики качества:

- `accuracy`;
- `f1`;
- `roc_auc`.

Quality gate задан в `config.ini`: `accuracy >= 0.65` и `f1 >= 0.65`.
Фактические значения после локального запуска demo pipeline:

- `accuracy = 0.866`;
- `f1 = 0.893`;
- `roc_auc = 0.948`.

Полный JSON сохраняется в `reports/metrics.json`.

## API

API реализован на FastAPI.

Методы:

- `GET /health` - статус сервиса;
- `GET /model` - информация о модели, признаках и метриках;
- `POST /predict` - предсказание атрибута `Smiling`.

## Тестирование

Код покрыт тестами на `pytest`:

- парсинг официального файла CelebA;
- demo-подготовка данных;
- обучение и оценка модели;
- smoke-тест API.

Команда запуска:

```bash
pytest
```

Результат проверки: `5 passed`, итоговое покрытие в pytest-отчете `79.26%`.

## DVC

DVC pipeline описан в `dvc.yaml` и содержит stages:

- `prepare`;
- `train`;
- `evaluate`.

Команда воспроизведения:

```bash
dvc repro
```

## Docker

Модель обернута в контейнер через `Dockerfile`.

Сборка:

```bash
docker build -t celeba-smiling-api:local .
```

Запуск:

```bash
docker compose up api
```

## CI

CI pipeline находится в `ci/Jenkinsfile` и `.github/workflows/ci.yml`.

Этапы:

1. checkout;
2. установка зависимостей;
3. `dvc repro`;
4. `pytest`;
5. сборка Docker image;
6. push image в DockerHub;
7. генерация `dev_sec_ops.yml`.

Запуск настроен на pull request в основную ветку.

## CD

CD pipeline находится в `cd/Jenkinsfile`.

Этапы:

1. запуск контейнера API;
2. запуск функциональных тестов внутри контейнера `cd-tests`;
3. сохранение `reports/functional_test_results.json`.

Сценарий тестирования описан в `scenario.json`.

## Результаты

Функциональное тестирование контейнера:

```text
passed = true
scenario = CelebA API smoke scenario
results file = reports/functional_test_results.json
```

Docker image после локальной сборки:

```text
celeba-smiling-api:local
sha256:381d83f275848b270db1e19543e9b5f2a337cfddc63bcec0beed477cc8cf6618
```

Ссылка на GitHub repository:

```text
TODO: вставить ссылку после push
```

Ссылка на DockerHub image:

```text
TODO: вставить ссылку после push image
```

Актуальный zip-дистрибутив:

```text
dist/celeba_smiling_mlops.zip
```
