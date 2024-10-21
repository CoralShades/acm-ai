.PHONY: run check ruff database lint docker-build docker-push

# Get version from pyproject.toml
VERSION := $(shell grep -m1 version pyproject.toml | cut -d'"' -f2)
IMAGE_NAME := lfnovo/open_notebook
database:
	docker compose up -d

run:
	poetry run streamlit run app_home.py

lint:
	poetry run python -m mypy .

ruff:
	ruff check . --fix

docker-build:
	docker build . -t $(IMAGE_NAME):$(VERSION)
	docker tag $(IMAGE_NAME):$(VERSION) $(IMAGE_NAME):latest

docker-push:
	docker push $(IMAGE_NAME):$(VERSION)
	docker push $(IMAGE_NAME):latest

# Combined build and push
docker-release: docker-build docker-push