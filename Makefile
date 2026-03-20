# ============================================
# KINVA MASTER - MAKEFILE
# ============================================

.PHONY: help install run web bot test clean deploy

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Run both web and bot"
	@echo "  make web        - Run web app only"
	@echo "  make bot        - Run bot only"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean temporary files"
	@echo "  make deploy     - Deploy to Render"

install:
	pip install -r requirements.txt

web:
	python src/app.py

bot:
	python src/bot.py

run:
	@echo "Starting web app and bot..."
	python src/app.py &
	python src/bot.py

test:
	pytest tests/ -v --cov=src

clean:
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf uploads/temp/*
	rm -rf logs/*.log
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

deploy:
	git push origin main
	@echo "Deployment triggered on Render"

docker-build:
	docker build -t kinva-master .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down
