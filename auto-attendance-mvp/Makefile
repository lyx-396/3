.PHONY: venv install run docker-build docker-up test

venv:
python3 -m venv .venv

install:
pip install -r requirements.txt

run:
FLASK_APP=app.py flask run --host=0.0.0.0 --port=5000

docker-build:
docker build -t auto-attendance-mvp .

docker-up:
docker-compose up --build

test:
pytest
