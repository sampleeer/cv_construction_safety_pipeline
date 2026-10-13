.PHONY: install download pipeline test lint typecheck api benchmark video docker-build compose-test
IMAGE ?= cv-mlops:local
install:
	python -m pip install -r requirements-export.txt -r requirements.txt
download:
	python scripts/download_model.py
	python -m src.helmet.download
pipeline:
	dvc repro
test:
	pytest
lint:
	ruff check src/cv src/helmet src/api/main.py tests/cv tests/helmet scripts/download_model.py scripts/smoke_cv.py scripts/demo_cv.py
typecheck:
	mypy src/helmet/events.py src/helmet/store.py src/helmet/dataset.py src/helmet/quality.py src/cv/detector.py src/cv/video.py src/cv/benchmark.py src/api/main.py
api:
	uvicorn src.api.main:app --host 127.0.0.1 --port 8000
benchmark:
	python -m src.cv.benchmark
video:
	python -m src.cv.video --source "$(SOURCE)"
docker-build:
	docker build -t $(IMAGE) .
compose-test:
	DOCKER_IMAGE=$(IMAGE) docker compose up --build --abort-on-container-exit --exit-code-from cd-tests cd-tests
