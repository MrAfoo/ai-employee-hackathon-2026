# Task Manager AI Employee - Makefile

.PHONY: help build push deploy-kind deploy-minikube deploy-helm clean test

# Variables
IMAGE_NAME := task-manager
IMAGE_TAG := latest
HELM_RELEASE := task-manager
NAMESPACE := default

help: ## Show this help message
	@echo "Task Manager AI Employee - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

docker-compose-up: ## Start with Docker Compose
	@echo "Starting with Docker Compose..."
	docker-compose up -d

docker-compose-down: ## Stop Docker Compose
	@echo "Stopping Docker Compose..."
	docker-compose down -v

deploy-kind: build ## Deploy to Kind cluster
	@echo "Loading image to Kind..."
	kind load docker-image $(IMAGE_NAME):$(IMAGE_TAG)
	@echo "Deploying to Kind..."
	kubectl apply -k k8s/
	@echo "Waiting for deployment..."
	kubectl wait --for=condition=ready pod -l app=task-manager --timeout=300s
	@echo "Deployment complete!"

deploy-minikube: ## Deploy to Minikube cluster
	@echo "Building in Minikube environment..."
	eval $$(minikube docker-env) && docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "Deploying to Minikube..."
	kubectl apply -k k8s/
	@echo "Waiting for deployment..."
	kubectl wait --for=condition=ready pod -l app=task-manager --timeout=300s
	@echo "Deployment complete!"

deploy-helm: build ## Deploy using Helm
	@echo "Loading image to Kind/Minikube..."
	kind load docker-image $(IMAGE_NAME):$(IMAGE_TAG) || true
	@echo "Installing with Helm..."
	helm upgrade --install $(HELM_RELEASE) ./helm --namespace $(NAMESPACE)
	@echo "Deployment complete!"

port-forward: ## Port forward to access service locally
	@echo "Port forwarding to localhost:8080..."
	kubectl port-forward svc/$(HELM_RELEASE) 8080:8080

test-health: ## Test health endpoint
	@echo "Testing health endpoint..."
	curl -f http://localhost:8080/health && echo "" || echo "Health check failed"

test-create-task: ## Create a test task
	@echo "Creating test task..."
	curl -X POST http://localhost:8080/api/v1/tasks \
		-H "Content-Type: application/json" \
		-d '{"title":"Test Task","description":"Automated test","deadline":"2026-02-20T17:00:00Z","priority":"high"}'
	@echo ""

test-list-tasks: ## List all tasks
	@echo "Listing all tasks..."
	curl http://localhost:8080/api/v1/tasks | python -m json.tool

logs: ## View application logs
	kubectl logs -f deployment/$(HELM_RELEASE) --tail=100

clean-kubectl: ## Clean up kubectl deployment
	kubectl delete -k k8s/ || true

clean-helm: ## Clean up Helm deployment
	helm uninstall $(HELM_RELEASE) || true
	kubectl delete pvc $(HELM_RELEASE)-pvc || true

clean: clean-helm clean-kubectl ## Clean up all deployments
	@echo "Cleanup complete!"

status: ## Show deployment status
	@echo "=== Pods ==="
	kubectl get pods -l app=task-manager
	@echo ""
	@echo "=== Services ==="
	kubectl get svc -l app=task-manager
	@echo ""
	@echo "=== PVCs ==="
	kubectl get pvc
	@echo ""
	@echo "=== CronJobs ==="
	kubectl get cronjobs

describe: ## Describe deployment resources
	kubectl describe deployment $(HELM_RELEASE)
	kubectl describe svc $(HELM_RELEASE)

all: build deploy-kind port-forward ## Build, deploy to Kind, and port-forward
