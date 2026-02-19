# Contributing to AI Employee Hackathon 2026

Thank you for your interest in contributing! 🎉 This guide will help you get started.

## 📋 Table of Contents
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/AI-Employee-Hackathon-2026.git
   cd AI-Employee-Hackathon-2026
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## How to Contribute

### 🐛 Reporting Bugs
- Use the **Bug Report** issue template
- Include steps to reproduce, expected vs actual behavior
- Attach logs or screenshots if possible

### 💡 Suggesting Features
- Use the **Feature Request** issue template
- Explain the use case and why it's valuable
- Keep it focused and specific

### 📝 Improving Documentation
- Fix typos, unclear explanations, or outdated content
- Add examples, diagrams, or better explanations

### 🔧 Fixing Bugs or Adding Features
- Check existing issues before starting work
- Comment on the issue to say you're working on it
- Keep changes focused — one feature/fix per PR

---

## Development Setup

### Prerequisites
- Docker Desktop
- Kind
- kubectl
- Helm
- Python 3.11+

### Local Setup
```bash
# Install dependencies
pip install -r Phase2-Code/task-manager/requirements-slim.txt

# Build Docker images
docker build -t task-manager:latest -f Phase2-Code/task-manager/Dockerfile.slim Phase2-Code/task-manager

# Create Kind cluster and deploy
kind create cluster --name ai-employee
.\deploy-all.ps1

# Start services
.\port-forward.ps1
```

### Running Tests
```bash
# Test Task Manager
curl http://localhost:8081/health

# Test Workflow Automation
curl http://localhost:8082/health

# Test Reporting Agent
curl http://localhost:8083/health
```

---

## Commit Guidelines

Use clear, descriptive commit messages following this format:

```
type(scope): short description

Examples:
feat(task-manager): add task priority endpoint
fix(workflow): fix port-forward issue
docs(readme): update quickstart steps
chore(helm): update resource limits
```

| Type | When to Use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `chore` | Maintenance/config |
| `refactor` | Code restructure |
| `test` | Adding tests |

---

## Pull Request Process

1. Ensure your branch is **up to date** with `main`
2. **Fill out** the PR template completely
3. Link the **related issue** in your PR description
4. Ensure all **services still work** after your changes
5. Request a **review** from a maintainer
6. PRs are merged after **1 approval**

### PR Checklist
- [ ] Code tested locally
- [ ] Documentation updated if needed
- [ ] No secrets or credentials committed
- [ ] Docker images build successfully
- [ ] All health endpoints return 200

---

## Questions?

Open a **Question** issue using the issue template, or reach out via:
📧 **contribute@ai-employee-hackathon.dev**

We appreciate every contribution, big or small! 🚀
