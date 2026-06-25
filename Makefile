.PHONY: install prepare train evaluate dvc test api docker-build compose-up compose-test devsecops dist clean

IMAGE ?= celeba-smiling-api:local

install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

prepare:
	python -m src.data.prepare --config config.ini

train:
	python -m src.models.train --config config.ini

evaluate:
	python -m src.models.evaluate --config config.ini

dvc:
	dvc repro

test:
	pytest

api:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000

docker-build:
	docker build -t $(IMAGE) .

compose-up:
	DOCKER_IMAGE=$(IMAGE) docker compose up --build api

compose-test:
	API_PORT=8001 DOCKER_IMAGE=$(IMAGE) docker compose up --build --abort-on-container-exit --exit-code-from cd-tests cd-tests

devsecops:
	python scripts/generate_dev_sec_ops.py --image $(IMAGE) --coverage coverage.xml --output dev_sec_ops.yml

dist:
	python scripts/create_dist.py --output dist/celeba_smiling_mlops.zip

clean:
	rm -rf .pytest_cache htmlcov coverage.xml .coverage dist
