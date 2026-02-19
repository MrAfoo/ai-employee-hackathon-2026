# Workflow Automation AI Employee - Makefile
# Quick commands for building, deploying, and managing the service

.PHONY: help build run stop clean deploy-docker deploy-kind deploy-helm port-forward logs test

# Default target
help:
	@echo "Workflow Automation AI Employee - Make Commands"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make build              - Build Docker image"
	@echo "  make run                - Run with docker-compose"
	@echo "  make stop               - Stop docker-compose"
	@echo "  make clean              - Clean up Docker resources"
	@echo ""
	@echo "Kubernetes Commands:"
	@echo "  make deploy-kind        - Deploy to Kind cluster"
	@echo "  make deploy-helm        - Deploy using Helm"
	@echo "  make port-forward       - Forward ports for local access"
	@echo "  make logs               - View application logs"
	@echo ""
	@echo "Development Commands:"
	@echo "  make test               - Run tests"
	@echo "  make lint               - Run code linting"

# Docker commands
build:
	docker build -t workflow-automation:latest .

run:
	docker-compose up -d
	@echo "Workflow Automation running at http://localhost:8080"

stop:
	docker-compose down

clean:
	docker-compose down -v
	docker rmi workflow-automation:latest || true

# Kubernetes with kubectl
deploy-kind:
	kubectl apply -k k8s/
	@echo "Waiting for deployment to be ready..."
	kubectl wait --for=condition=available --timeout=300s deployment/workflow-automation

delete-kind:
	kubectl delete -k k8s/

# Kubernetes with Helm
deploy-helm:
	helm upgrade --install workflow-automation ./helm \
		--create-namespace \
		--wait \
		--timeout 5m
	@echo "Workflow Automation deployed via Helm"

delete-helm:
	helm uninstall workflow-automation

# Access commands
port-forward:
	@echo "Forwarding ports..."
	@echo "  - API: http://localhost:8080"
	@echo "  - Metrics: http://localhost:9090"
	kubectl port-forward svc/workflow-automation 8080:8080 9090:9090

logs:
	kubectl logs -f deployment/workflow-automation

# Workflow commands
trigger-workflow:
	curl -X POST http://localhost:8080/workflows/example-workflow/trigger \
		-H "Content-Type: application/json" \
		-d '{"parameters": {"input_data": "test"}}'

list-workflows:
	curl http://localhost:8080/workflows

# Development commands
test:
	pytest tests/ -v

lint:
	ruff check src/
	black --check src/

format:
	black src/
	ruff check --fix src/

# Health check
health:
	curl http://localhost:8080/health

# Full deployment (Docker Compose)
deploy-docker: build run
	@echo "Deployment complete!"
	@echo "Access the service at http://localhost:8080"
	@echo "Run 'make logs' to view logs"

# Full deployment (Kubernetes)
deploy-k8s: deploy-kind port-forward

# Cleanup everything
clean-all: clean delete-kind delete-helm
	@echo "All resources cleaned up"
