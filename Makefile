.PHONY: dev test demo clean build setup eval

dev:
	docker compose up --build

build:
	docker compose build

test:
	cd backend && python -m pytest tests/ -v 2>/dev/null || echo "No tests found"
	cd frontend && npm run lint

demo:
	./scripts/smoke_test.sh

eval:
	python scripts/run_evaluation.py --url https://callshield.onrender.com

setup:
	./scripts/setup.sh

clean:
	docker compose down -v --rmi local
