# WillGPT Podman Development Makefile

.PHONY: help build up down restart logs shell test clean

# Default target
help:
	@echo "WillGPT Podman Commands:"
	@echo ""
	@echo "  make build          - Build container images"
	@echo "  make up             - Start all services"
	@echo "  make up-jupyter     - Start services with Jupyter notebook"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-app       - View app container logs"
	@echo "  make logs-qdrant    - View Qdrant logs"
	@echo "  make shell          - Open shell in app container"
	@echo "  make test-qdrant    - Test Qdrant connection"
	@echo "  make test-parser    - Test ChatGPT parser"
	@echo "  make merge          - Run merge_and_upload.py"
	@echo "  make search         - Open interactive search"
	@echo "  make clean          - Stop services and remove volumes"
	@echo "  make rebuild        - Clean rebuild everything"
	@echo ""

# Build images
build:
	podman-compose build

# Start services
up:
	podman-compose up -d
	@echo "Services started. Access Qdrant at http://localhost:6333/dashboard"

# Start with Jupyter
up-jupyter:
	podman-compose --profile jupyter up -d
	@echo "Services started with Jupyter at http://localhost:8888"

# Stop services
down:
	podman-compose down

# Restart services
restart:
	podman-compose restart

# View logs
logs:
	podman-compose logs -f

logs-app:
	podman-compose logs -f willgpt-app

logs-qdrant:
	podman-compose logs -f qdrant

# Open shell
shell:
	podman exec -it willgpt-app /bin/bash

# Test Qdrant connection
test-qdrant:
	podman exec willgpt-app python test_qdrant_connection.py

# Test parser
test-parser:
	@if [ ! -f data/raw/chatgpt.json ]; then \
		echo "Error: data/raw/chatgpt.json not found"; \
		exit 1; \
	fi
	podman exec willgpt-app python test_parser.py data/raw/chatgpt.json

# Test Claude parser
test-claude:
	@if [ ! -f data/raw/claude.json ]; then \
		echo "Error: data/raw/claude.json not found"; \
		exit 1; \
	fi
	podman exec willgpt-app python test_parser.py data/raw/claude.json

# Run merge and upload
merge:
	podman exec -it willgpt-app python merge_and_upload.py

# Interactive search
search:
	podman exec -it willgpt-app python retrieval/search_qdrant.py

# Single search query (usage: make query QUERY="your search here")
query:
	@if [ -z "$(QUERY)" ]; then \
		echo "Usage: make query QUERY=\"your search query\""; \
		exit 1; \
	fi
	podman exec willgpt-app python retrieval/search_qdrant.py "$(QUERY)" --limit 10

# Clean up (removes volumes - DELETES QDRANT DATA)
clean:
	podman-compose down -v
	@echo "Cleaned up containers and volumes"

# Full rebuild
rebuild: clean
	podman-compose build --no-cache
	podman-compose up -d
	@echo "Full rebuild complete"

# Check service health
health:
	@echo "Checking service health..."
	@curl -s http://localhost:6333/health || echo "Qdrant not responding"
	@podman ps --filter "name=willgpt" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View Qdrant collections
collections:
	@curl -s http://localhost:6333/collections | python -m json.tool

# Stats
stats:
	podman stats --no-stream

# Show data directory sizes
data-size:
	@echo "Data directory sizes:"
	@du -sh data/raw data/processed 2>/dev/null || echo "No data directories found"
	@echo ""
	@echo "Container volumes:"
	@podman volume ls --format "table {{.Name}}\t{{.Driver}}\t{{.Mountpoint}}"

# Development: watch logs during development
dev:
	podman-compose up -d
	podman-compose logs -f willgpt-app
