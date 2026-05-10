.PHONY: help test smoke probe install lint

help:
	@echo "Targets:"
	@echo "  install    Install deps via uv pip"
	@echo "  test       Run pytest"
	@echo "  probe      Verify Vertex AI connectivity"
	@echo "  smoke      Run smoke-test-4page pipeline (interactive)"
	@echo "  lint       Run ruff if installed"

install:
	uv pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

probe:
	python -c "from tools.image.vertex_gemini_image import VertexGeminiImage; VertexGeminiImage().probe()"

lint:
	ruff check . || echo "ruff not installed; skip"
