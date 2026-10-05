# DevSecOps CI/CD Platform

## Overview

A production-oriented Python API platform designed to demonstrate modern DevOps and DevSecOps practices across the software delivery lifecycle.

The project is being developed incrementally, starting with application development, testing, containerization, and continuous integration before introducing security scanning, cloud infrastructure, infrastructure as code, observability, deployment automation, and failure recovery.

## Problem Statement

The goal of this project is to build a reproducible application delivery platform that demonstrates how a software application can move from source code to a production-oriented runtime through automated and secure engineering practices.

The platform is intentionally developed in stages so that each layer can be implemented, tested, verified, and documented before additional infrastructure is introduced.

## Architecture

### Current Architecture

```text
Developer
    |
    | git push / Pull Request
    v
GitHub Repository
    |
    +----------------------+
    |                      |
    v                      v
GitHub Actions         Source Code
    |
    v
Ubuntu Runner
    |
    +--> Python 3.12
    |
    +--> Install Dependencies
    |
    +--> Run pytest
    |
    +--> Coverage Report
    |
    v
Pass / Fail

Source Code
    |
    v
Python Flask Application
    |
    v
Gunicorn WSGI Server
    |
    v
Docker Container
    |
    +--> Health Check
    |
    +--> Non-root application user
    |
    v
Local Host :5000
```

The architecture will evolve as security scanning, cloud infrastructure, infrastructure as code, deployment automation, and monitoring are introduced.

## Technology Stack

### Current

- Python 3.12
- Flask 3.1.3
- Gunicorn 23.0.0
- Docker
- pytest
- pytest-cov
- Git
- GitHub
- GitHub Actions
- Ubuntu GitHub-hosted runners

### Planned

- Docker image security scanning
- AWS
- Amazon ECR
- Terraform
- Infrastructure security controls
- Monitoring and observability
- Failure recovery mechanisms
- Automated cloud deployment

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration (CI).

The current pipeline validates application changes and performs a dependency security audit before changes are considered ready for integration.

### CI Workflow

The workflow is triggered by:

- Pushes to the `main` branch
- Pull requests targeting the `main` branch

The pipeline runs on a GitHub-hosted Ubuntu runner and performs the following steps:

1. Checks out the repository.
2. Sets up Python 3.12.
3. Restores the pip dependency cache.
4. Installs application and development dependencies.
5. Installs the pinned `pip-audit` security scanner.
6. Audits production dependencies for known vulnerabilities.
7. Runs the automated pytest test suite.
8. Generates a terminal coverage report.

### Current CI Flow

```text
Developer
    |
    | git push / Pull Request
    v
GitHub Actions
    |
    v
Ubuntu Runner
    |
    +--> Checkout Repository
    |
    +--> Python 3.12
    |
    +--> Restore pip Cache (if available)
    |
    +--> Install Dependencies
    |
    +--> Dependency Security Audit
    |       |
    |       +--> pip-audit
    |       |
    |       +--> Pass / Fail
    |
    +--> Run pytest
    |
    +--> Coverage Report
    |
    v
Pass / Fail
```

### CI Validation Results

The current test suite contains three automated tests covering the application's API endpoints.

Latest successful CI run:

```text
Tests:       3 passed
Coverage:    92%
Python:      3.12.14
Platform:    Ubuntu Linux
```

The CI workflow has also been deliberately tested against a failing test condition.

An incorrect expected HTTP status code caused pytest to return exit code `1`, which correctly caused the GitHub Actions workflow to fail. After correcting the test assertion, the workflow successfully returned to a passing state.

This validates both the normal and failure paths of the CI pipeline.

### Workflow Definition

The GitHub Actions workflow is located at:

```text
.github/workflows/ci.yml
```

The current CI implementation focuses on automated testing and validation. Container image building, security scanning, infrastructure provisioning, deployment, and production monitoring will be introduced in later stages of the project.

## Security

Current security controls include:

- Production container runs as a dedicated non-root user (`appuser`).
- Development dependencies are separated from production dependencies.
- Docker build context is restricted using `.dockerignore`.
- The container includes an application health check.
- The runtime image uses the lightweight `python:3.12-slim` base image.

Future security improvements will include automated dependency and container vulnerability scanning, image hardening, secrets management, and infrastructure security controls.

## Infrastructure

Infrastructure automation has not yet been implemented.

The current application can be run locally using Python or Docker.

Future infrastructure will include cloud deployment and Infrastructure as Code using Terraform.

## Deployment

### Local Python Deployment

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the application:

```bash
python -m app.main
```

The application listens on:

```text
http://localhost:5000
```

### Docker Deployment

Build the production-oriented container image:

```bash
docker build -t devsecops-cicd-platform:1.0.0 .
```

Run the container:

```bash
docker run -d \
  --name devsecops-platform \
  -p 5000:5000 \
  devsecops-cicd-platform:1.0.0
```

Verify the running container:

```bash
docker ps
```

The container should report a healthy status after the configured health check succeeds.

## Testing

The application currently has three API tests covering:

- `/health`
- `/api/v1/status`
- `/api/v1/info`

Run the test suite:

```bash
pytest
```

Current result:

```text
3 tests passed
92% code coverage
```

Generate a coverage report:

```bash
pytest --cov=app
```

### Container Verification

The Dockerized application was also verified independently.

#### Health Endpoint

```bash
curl http://localhost:5000/health
```

Expected result:

```json
{
  "service": "devsecops-cicd-platform",
  "status": "healthy"
}
```

#### Status Endpoint

```bash
curl http://localhost:5000/api/v1/status
```

Expected result:

```json
{
  "status": "operational",
  "version": "1.0.0"
}
```

#### Information Endpoint

```bash
curl http://localhost:5000/api/v1/info
```

Expected result:

```json
{
  "application": "DevSecOps CI/CD Platform",
  "environment": "development",
  "version": "1.0.0"
}
```

### Container Security Verification

The application container was verified to run as:

```text
appuser
```

rather than the root user.

The Docker health check was also verified with:

```text
Status: healthy
FailingStreak: 0
```

Gunicorn successfully started two workers inside the container.

## Monitoring

Application monitoring and centralized observability have not yet been implemented.

The current container provides a basic operational health check through the `/health` endpoint.

Future improvements will include:

- Application metrics
- Structured logging
- Monitoring
- Alerting
- Centralized log collection

## Failure Recovery

Automated failure recovery has not yet been implemented.

Current operational verification is provided through:

- Docker health checks
- Application health endpoint
- Gunicorn process logging
- Container status inspection

Future iterations will introduce deployment recovery mechanisms and infrastructure-level health monitoring.

## Project Structure

```text
devsecops-cicd-platform/
├── app/
│   ├── __init__.py
│   └── main.py
├── tests/
│   └── test_api.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
├── .dockerignore
├── .gitignore
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12+
- Docker
- Git

### Clone the Repository

```bash
git clone https://github.com/markfosu/devsecops-cicd-platform.git
cd devsecops-cicd-platform
```

### Run Tests Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

### Run with Docker

```bash
docker build -t devsecops-cicd-platform:1.0.0 .

docker run -d \
  --name devsecops-platform \
  -p 5000:5000 \
  devsecops-cicd-platform:1.0.0
```

Verify:

```bash
curl http://localhost:5000/health
```

## Lessons Learned

### Runtime Reproducibility

The project uses Python 3.12 and an isolated virtual environment for local development. Docker provides a separate, reproducible runtime environment for the application.

### Production Application Serving

Flask's development server is useful during development, but the container uses Gunicorn as the production WSGI server.

### Container Security

The application does not require root privileges, so the container runs using a dedicated `appuser`.

### Docker Layer Caching

The dependency file is copied before the application source code so Docker can reuse the dependency installation layer when application code changes.

### Health Checks

A running container does not necessarily mean that the application is functioning correctly. The Docker health check verifies that the application's `/health` endpoint is responding successfully.

### Continuous Integration

Automated CI provides repeatable validation in a clean environment. The project demonstrated both successful and failing CI runs, including diagnosis and recovery from a deliberately introduced test failure.

### Incremental Engineering

Each stage of the project is implemented and verified before additional complexity is introduced. This reduces troubleshooting scope and creates evidence for each engineering decision.

## Future Improvements

Planned improvements include:

1. Docker image security scanning
2. Dependency vulnerability scanning
3. Container image publishing
4. AWS deployment
5. Terraform infrastructure
6. Automated cloud deployment
7. Application and infrastructure monitoring
8. Centralized logging
9. Failure recovery and rollback mechanisms
10. Production security hardening
11. Multi-environment deployment
12. Deployment documentation and architecture diagrams
