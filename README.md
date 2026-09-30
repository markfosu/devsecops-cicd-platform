# DevSecOps CI/CD Platform

## Overview

A production-oriented Python API platform designed to demonstrate modern DevOps and DevSecOps practices across the software delivery lifecycle.

The project is being developed incrementally, starting with application development and containerization before introducing automated CI/CD, security scanning, cloud infrastructure, infrastructure as code, observability, and failure recovery.

Problem Statement
-----------------

The goal of this project is to build a reproducible application delivery platform that demonstrates how a software application can move from source code to a production-oriented runtime through automated and secure engineering practices.

The platform is intentionally developed in stages so that each layer can be implemented, tested, verified, and documented before additional infrastructure is introduced.

Architecture
------------

Current architecture:

```
Developer
   |
   v
Git Repository
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

The architecture will evolve as CI/CD, security scanning, AWS infrastructure, infrastructure as code, and monitoring are introduced.

Technology Stack
----------------

### Current

-   Python 3.12

-   Flask 3.1.1

-   Gunicorn 23.0.0

-   Docker

-   pytest

-   pytest-cov

-   Git/GitHub

### Planned

-   GitHub Actions

-   Docker image security scanning

-   AWS

-   Amazon ECR

-   Terraform

-   Infrastructure security controls

-   Monitoring and observability

-   Failure recovery mechanisms

CI/CD Pipeline
--------------

CI/CD automation has not yet been implemented.

The planned delivery flow is:

```
Git Push
   |
   v
Automated Tests
   |
   v
Security Checks
   |
   v
Docker Build
   |
   v
Container Image Scan
   |
   v
Container Registry
   |
   v
Infrastructure Deployment
   |
   v
Application Verification

```

Security
--------

Current security controls include:

-   Production container runs as a dedicated non-root user (`appuser`).

-   Development dependencies are separated from production dependencies.

-   Docker build context is restricted using `.dockerignore`.

-   The container includes an application health check.

-   The runtime image uses the lightweight `python:3.12-slim` base image.

Future security improvements will include automated dependency and container vulnerability scanning, image hardening, secrets management, and infrastructure security controls.

Infrastructure
--------------

Infrastructure automation has not yet been implemented.

The current application can be run locally using Python or Docker.

Future infrastructure will include cloud deployment and Infrastructure as Code using Terraform.

Deployment
----------

### Local Python Deployment

Create and activate a virtual environment:

```
python3 -m venv .venv
source .venv/bin/activate

```

Install development dependencies:

```
pip install -r requirements-dev.txt

```

Run the application:

```
python -m app.main

```

The application listens on:

```
http://localhost:5000

```

### Docker Deployment

Build the production-oriented container image:

```
docker build -t devsecops-cicd-platform:1.0.0 .

```

Run the container:

```
docker run -d\
  --name devsecops-platform\
  -p 5000:5000\
  devsecops-cicd-platform:1.0.0

```

Verify the running container:

```
docker ps

```

The container should report a healthy status after the configured health check succeeds.

Testing
-------

The application currently has three API tests covering:

-   `/health`

-   `/api/v1/status`

-   `/api/v1/info`

Test suite:

```
pytest

```

Current result:

```
3 tests passed
92% code coverage

```

Coverage can be generated with:

```
pytest --cov=app

```

### Container Verification

The Dockerized application was also verified independently.

Health endpoint:

```
curl http://localhost:5000/health

```

Result:

```
{
  "service": "devsecops-cicd-platform",
  "status": "healthy"
}

```

Status endpoint:

```
curl http://localhost:5000/api/v1/status

```

Result:

```
{
  "status": "operational",
  "version": "1.0.0"
}

```

Information endpoint:

```
curl http://localhost:5000/api/v1/info

```

Result:

```
{
  "application": "DevSecOps CI/CD Platform",
  "environment": "development",
  "version": "1.0.0"
}

```

### Container Security Verification

The application container was verified to run as:

```
appuser

```

rather than the root user.

The Docker health check was also verified with:

```
Status: healthy
FailingStreak: 0

```

Gunicorn successfully started two workers inside the container.

Monitoring
----------

Application monitoring and centralized observability have not yet been implemented.

The current container provides a basic operational health check through the `/health` endpoint.

Future improvements will include application metrics, structured logging, monitoring, alerting, and centralized log collection.

Failure Recovery
----------------

Automated failure recovery has not yet been implemented.

Current operational verification is provided through:

-   Docker health checks

-   Application health endpoint

-   Gunicorn process logging

-   Container status inspection

Future iterations will introduce deployment recovery mechanisms and infrastructure-level health monitoring.

Project Structure
-----------------

```
devsecops-cicd-platform/
├── app/
│   ├── __init__.py
│   └── main.py
├── tests/
│   └── test_api.py
├── .github/
│   └── workflows/
├── docs/
├── .dockerignore
├── .gitignore
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md

```

Getting Started
---------------

### Prerequisites

-   Python 3.12+

-   Docker

-   Git

### Clone the repository

```
git clone https://github.com/markfosu/devsecops-cicd-platform.git
cd devsecops-cicd-platform

```

### Run tests locally

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest

```

### Run with Docker

```
docker build -t devsecops-cicd-platform:1.0.0 .

docker run -d\
  --name devsecops-platform\
  -p 5000:5000\
  devsecops-cicd-platform:1.0.0

```

Verify:

```
curl http://localhost:5000/health

```

Lessons Learned
---------------

### Runtime reproducibility

The project uses Python 3.12 and an isolated virtual environment for local development. Docker provides a separate, reproducible runtime environment for the application.

### Production application serving

Flask's development server is useful during development, but the container uses Gunicorn as the production WSGI server.

### Container security

The application does not require root privileges, so the container runs using a dedicated `appuser`.

### Docker layer caching

The dependency file is copied before the application source code so Docker can reuse the dependency installation layer when application code changes.

### Health checks

A running container does not necessarily mean that the application is functioning correctly. The Docker health check verifies that the application's `/health` endpoint is responding successfully.

### Incremental engineering

Each stage of the project is being implemented and verified before additional complexity is introduced. This reduces troubleshooting scope and creates evidence for each engineering decision.

Future Improvements
-------------------

Planned improvements include:

1.  GitHub Actions CI pipeline

2.  Automated unit testing on every push

3.  Docker image security scanning

4.  Dependency vulnerability scanning

5.  Container image publishing

6.  AWS deployment

7.  Terraform infrastructure

8.  Automated cloud deployment

9.  Application and infrastructure monitoring

10.  Centralized logging

11.  Failure recovery and rollback mechanisms

12.  Production security hardening

13.  Multi-environment deployment

14.  Deployment documentation and architecture diagrams