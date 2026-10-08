PY ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: test backend frontend contract
test:
	$(PY) -m pytest -q backend
	cd frontend && npm run build

backend:
	$(PY) -m uvicorn backend.api.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

contract:
	$(PY) -c "import json; from backend.api.main import app; print(json.dumps(app.openapi(), indent=1))" > docs/openapi.json
