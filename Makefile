.PHONY: run frontend check ruff database lint api start-all stop-all status clean-cache worker worker-start worker-stop worker-restart
.PHONY: docker-buildx-prepare docker-buildx-clean docker-buildx-reset
.PHONY: docker-push docker-push-latest docker-release tag export-docs
.PHONY: smart-start smart-stop health fix preflight tmux

# Get version from pyproject.toml
VERSION := $(shell grep -m1 version pyproject.toml | cut -d'"' -f2)

# Image names for both registries
DOCKERHUB_IMAGE := lfnovo/open_notebook
GHCR_IMAGE := ghcr.io/lfnovo/open-notebook

# Build platforms
PLATFORMS := linux/amd64,linux/arm64

database:
	docker compose up -d surrealdb

run:
	@echo "⚠️  Warning: Starting frontend only. For full functionality, use 'make start-all'"
	cd frontend && npm run dev

frontend:
	cd frontend && npm run dev

lint:
	uv run python -m mypy .

ruff:
	ruff check . --fix

# === Docker Build Setup ===
docker-buildx-prepare:
	@docker buildx inspect multi-platform-builder >/dev/null 2>&1 || \
		docker buildx create --use --name multi-platform-builder --driver docker-container
	@docker buildx use multi-platform-builder

docker-buildx-clean:
	@echo "🧹 Cleaning up buildx builders..."
	@docker buildx rm multi-platform-builder 2>/dev/null || true
	@docker ps -a | grep buildx_buildkit | awk '{print $$1}' | xargs -r docker rm -f 2>/dev/null || true
	@echo "✅ Buildx cleanup complete!"

docker-buildx-reset: docker-buildx-clean docker-buildx-prepare
	@echo "✅ Buildx reset complete!"

# === Docker Build Targets ===

# Build and push version tags ONLY (no latest) for both regular and single images
docker-push: docker-buildx-prepare
	@echo "📤 Building and pushing version $(VERSION) to both registries..."
	@echo "🔨 Building regular image..."
	docker buildx build --pull \
		--platform $(PLATFORMS) \
		--progress=plain \
		-t $(DOCKERHUB_IMAGE):$(VERSION) \
		-t $(GHCR_IMAGE):$(VERSION) \
		--push \
		.
	@echo "🔨 Building single-container image..."
	docker buildx build --pull \
		--platform $(PLATFORMS) \
		--progress=plain \
		-f Dockerfile.single \
		-t $(DOCKERHUB_IMAGE):$(VERSION)-single \
		-t $(GHCR_IMAGE):$(VERSION)-single \
		--push \
		.
	@echo "✅ Pushed version $(VERSION) to both registries (latest NOT updated)"
	@echo "  📦 Docker Hub:"
	@echo "    - $(DOCKERHUB_IMAGE):$(VERSION)"
	@echo "    - $(DOCKERHUB_IMAGE):$(VERSION)-single"
	@echo "  📦 GHCR:"
	@echo "    - $(GHCR_IMAGE):$(VERSION)"
	@echo "    - $(GHCR_IMAGE):$(VERSION)-single"

# Update v1-latest tags to current version (both regular and single images)
docker-push-latest: docker-buildx-prepare
	@echo "📤 Updating v1-latest tags to version $(VERSION)..."
	@echo "🔨 Building regular image with latest tag..."
	docker buildx build --pull \
		--platform $(PLATFORMS) \
		--progress=plain \
		-t $(DOCKERHUB_IMAGE):$(VERSION) \
		-t $(DOCKERHUB_IMAGE):v1-latest \
		-t $(GHCR_IMAGE):$(VERSION) \
		-t $(GHCR_IMAGE):v1-latest \
		--push \
		.
	@echo "🔨 Building single-container image with latest tag..."
	docker buildx build --pull \
		--platform $(PLATFORMS) \
		--progress=plain \
		-f Dockerfile.single \
		-t $(DOCKERHUB_IMAGE):$(VERSION)-single \
		-t $(DOCKERHUB_IMAGE):v1-latest-single \
		-t $(GHCR_IMAGE):$(VERSION)-single \
		-t $(GHCR_IMAGE):v1-latest-single \
		--push \
		.
	@echo "✅ Updated v1-latest to version $(VERSION)"
	@echo "  📦 Docker Hub:"
	@echo "    - $(DOCKERHUB_IMAGE):$(VERSION) → v1-latest"
	@echo "    - $(DOCKERHUB_IMAGE):$(VERSION)-single → v1-latest-single"
	@echo "  📦 GHCR:"
	@echo "    - $(GHCR_IMAGE):$(VERSION) → v1-latest"
	@echo "    - $(GHCR_IMAGE):$(VERSION)-single → v1-latest-single"

# Full release: push version AND update latest tags
docker-release: docker-push-latest
	@echo "✅ Full release complete for version $(VERSION)"

tag:
	@version=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	echo "Creating tag v$$version"; \
	git tag "v$$version"; \
	git push origin "v$$version"


dev:
	docker compose -f docker-compose.dev-local.yml up --build

full:
	docker compose -f docker-compose.full.yml up --build 


api:
	uv run run_api.py

# === Worker Management ===
.PHONY: worker worker-start worker-stop worker-restart

worker: worker-start

worker-start:
	@echo "Starting surreal-commands worker..."
	uv run --env-file .env surreal-commands-worker --import-modules commands

worker-stop:
	@echo "Stopping surreal-commands worker..."
	pkill -f "surreal-commands-worker" || true

worker-restart: worker-stop
	@sleep 2
	@$(MAKE) worker-start

# === Service Management ===
start-all:
	@echo "🚀 Starting ACM-AI (Database + API + Worker + Frontend)..."
	@echo "📊 Starting SurrealDB..."
	@docker compose up -d surrealdb
	@sleep 3
	@echo "🔧 Starting API backend (port 5055)..."
	@nohup uv run python run_api.py > /tmp/acm-ai-api.log 2>&1 & echo $$! > /tmp/acm-ai-api.pid
	@sleep 3
	@echo "⚙️ Starting background worker..."
	@nohup uv run surreal-commands-worker --import-modules commands > /tmp/acm-ai-worker.log 2>&1 & echo $$! > /tmp/acm-ai-worker.pid
	@sleep 2
	@echo "🌐 Starting Next.js frontend (port 8502)..."
	@echo "✅ All services started!"
	@echo "📱 Frontend: http://localhost:8502"
	@echo "🔗 API: http://localhost:5055"
	@echo "📚 API Docs: http://localhost:5055/docs"
	@echo ""
	@echo "📋 Logs available at:"
	@echo "  API:    tail -f /tmp/acm-ai-api.log"
	@echo "  Worker: tail -f /tmp/acm-ai-worker.log"
	@echo ""
	cd frontend && PORT=8502 npm run dev -- -p 8502

stop-all:
	@echo "🛑 Stopping all ACM-AI services..."
	@pkill -f "npm run dev.*8502" || true
	@pkill -f "next dev" || true
	@pkill -f "surreal-commands-worker" || true
	@pkill -f "run_api.py" || true
	@pkill -f "uvicorn api.main:app" || true
	@[ -f /tmp/acm-ai-frontend.pid ] && kill $$(cat /tmp/acm-ai-frontend.pid) 2>/dev/null || true
	@[ -f /tmp/acm-ai-worker.pid ] && kill $$(cat /tmp/acm-ai-worker.pid) 2>/dev/null || true
	@[ -f /tmp/acm-ai-api.pid ] && kill $$(cat /tmp/acm-ai-api.pid) 2>/dev/null || true
	@rm -f /tmp/acm-ai-*.pid 2>/dev/null || true
	@docker compose down
	@echo "✅ All services stopped!"

status:
	@echo "📊 ACM-AI Service Status:"
	@echo ""
	@echo "Database (SurrealDB):"
	@docker compose ps surrealdb 2>/dev/null | grep -q "Up" && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo ""
	@echo "API Backend (port 5055):"
	@curl -s http://localhost:5055/health >/dev/null 2>&1 && echo "  ✅ Running (healthy)" || echo "  ❌ Not running"
	@echo ""
	@echo "Background Worker:"
	@pgrep -f "surreal-commands-worker" >/dev/null && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo ""
	@echo "Frontend (port 8502):"
	@curl -s http://localhost:8502 >/dev/null 2>&1 && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo ""

# === Smart Service Management ===
smart-start:
	@uv run python scripts/service_manager.py start --auto-fix

smart-stop:
	@uv run python scripts/service_manager.py stop

health:
	@uv run python scripts/service_manager.py health

fix:
	@uv run python scripts/service_manager.py fix --auto-fix

preflight:
	@uv run python scripts/service_manager.py check

tmux:
	./start-all-tmux.sh

# === Documentation Export ===
export-docs:
	@echo "📚 Exporting documentation..."
	@uv run python scripts/export_docs.py
	@echo "✅ Documentation export complete!"

# === Cleanup ===
clean-cache:
	@echo "🧹 Cleaning cache directories..."
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".mypy_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -type f -delete 2>/dev/null || true
	@find . -name "*.pyo" -type f -delete 2>/dev/null || true
	@find . -name "*.pyd" -type f -delete 2>/dev/null || true
	@echo "✅ Cache directories cleaned!"