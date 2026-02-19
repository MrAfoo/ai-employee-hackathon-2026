# Workflow Automation AI Employee Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for workflow execution
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY workflows/ ./workflows/

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data /app/workflows

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WORKFLOW_DATA_DIR=/app/data
ENV WORKFLOW_LOG_DIR=/app/logs
ENV WORKFLOW_DEFINITIONS_DIR=/app/workflows
ENV WORKFLOW_PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-m", "src.main"]
