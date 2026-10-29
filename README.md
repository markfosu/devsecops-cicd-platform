# DevSecOps CI/CD Platform

A Python Flask API project demonstrating secure software delivery
through automated testing, dependency auditing, container vulnerability
scanning, infrastructure as code, and gated container publishing to
Amazon ECR.

## Overview

This project is developed incrementally. The application and container
run locally, while GitHub Actions validates code, scans dependencies and
container images, and publishes qualifying CI images to a private Amazon
ECR repository. Terraform manages the ECR repository, and GitHub Actions
uses AWS OpenID Connect (OIDC) for short-lived AWS credentials.

**Current scope:** CI/CD and container image publishing are implemented.
The application has **not** been deployed to AWS compute.

## Problem Statement

The goal is to demonstrate how an application can move from source code
to a tested, security-checked container image using repeatable
automation and least-privilege cloud access. Each stage is validated and
documented before additional infrastructure is introduced.

## Architecture

### Current delivery flow

``` text
Developer
   |
   v
GitHub repository (push / pull request)
   |
   v
GitHub Actions
   |
   +--> Test job
   |      +--> Python 3.12
   |      +--> Install dependencies
   |      +--> pip-audit production dependencies
   |      +--> pytest and coverage
   |
   +--> Container-scan job
   |      +--> Build Docker image
   |      +--> Trivy vulnerability scan
   |
   v
Required checks pass
   |
   +--> On push to main only:
          +--> GitHub Actions OIDC authentication to AWS
          +--> Push image to private Amazon ECR
          +--> Tag: git-<full-commit-sha>

Application runtime (local)
   |
   v
Flask API --> Gunicorn --> Docker container
                           +--> non-root appuser
                           +--> health check
                           +--> localhost:5000
```

The CI publishing job depends on the test and container-scan jobs. A
passing pull request does not itself publish an image; publishing is
restricted to qualifying pushes to `main`.

## Technology Stack

### Implemented

-   Python 3.12
-   Flask 3.1.3
-   Gunicorn 23.0.0
-   Docker
-   pytest and pytest-cov
-   pip-audit for Python dependency auditing
-   Trivy for container image vulnerability scanning
-   Git and GitHub
-   GitHub Actions and Ubuntu GitHub-hosted runners
-   Terraform for Amazon ECR repository provisioning
-   Amazon ECR for private container image storage
-   AWS IAM and GitHub Actions OIDC for CI authentication

### Planned

-   Application deployment to AWS compute
-   Application and infrastructure monitoring
-   Centralized logging and alerting
-   Automated deployment rollback and recovery
-   Multi-environment deployment

## CI/CD Pipeline

The workflow is defined in `.github/workflows/ci.yml` and runs for
pushes to `main` and pull requests targeting `main`.

### Validation and security stages

1.  Check out the repository.
2.  Set up Python 3.12 and restore the pip cache when available.
3.  Install application and development dependencies.
4.  Run `pip-audit` against production dependencies.
5.  Run the pytest suite and generate a coverage report.
6.  Build the container image.
7.  Scan the image with Trivy for High and Critical vulnerabilities.
8.  Fail the scan gate for matching findings with available fixes.
9.  For pushes to `main` that pass the required jobs, authenticate to
    AWS through OIDC and push the image to ECR.

The Trivy scan is configured with `ignore-unfixed: true`. This means
findings for which the scanner does not identify an available fix are
excluded from the failing gate; it does **not** mean those findings are
harmless or that the image has no vulnerabilities.

### CI validation evidence

Previously recorded successful results:

``` text
Tests:       3 passed
Coverage:    92%
Python:      3.12
Platform:    Ubuntu Linux
```

The workflow has also been tested with an intentionally incorrect
expected HTTP status code. Pytest returned exit code `1`, and the
workflow failed as expected. After the assertion was corrected, the
workflow returned to a passing state.

These are previously recorded results; check the latest GitHub Actions
run for current status.

## Security

### Application and container controls

-   The application container runs as the dedicated non-root user
    `appuser`.
-   Development dependencies are separated from production dependencies.
-   `.dockerignore` limits the Docker build context.
-   The container has a health check.
-   The runtime image uses `python:3.12-slim`.
-   Available operating system package upgrades are applied during image
    build.
-   `pip` is removed from the runtime image after dependency
    installation.
-   `pip-audit` audits production Python dependencies in CI.
-   Trivy scans container images in CI before publishing.

### Container vulnerability assessment

An earlier local Trivy scan of `devsecops-cicd-platform:1.0.5` reported:

-   **Unfiltered scan:** 44 High-severity findings and 0 Critical
    findings against Debian 13.7.
-   **Python packages:** no High or Critical findings in the scanned
    Python package metadata.
-   **Filtered scan:** no High or Critical findings were reported with
    `--ignore-unfixed`.

The unfiltered findings included repeated package-level reports for some
CVEs. The filtered scan excludes findings for which Trivy does not
identify an available fix. Neither result establishes that the image is
vulnerability-free. Operating system findings should be reassessed as
base-image and package security updates become available.

### AWS authentication and permissions

GitHub Actions assumes a dedicated AWS IAM role using OIDC rather than
storing long-lived AWS access keys in GitHub repository secrets. The
trust policy restricts the intended GitHub repository and `main` branch,
and the role's ECR permissions are scoped to the target repository and
required publishing operations.

## Infrastructure

Terraform provisions the private Amazon ECR repository. Its configured
controls include:

-   Immutable image tags
-   Image scanning on push
-   AES-256 encryption

The ECR repository is:

``` text
095453158828.dkr.ecr.us-east-1.amazonaws.com/devsecops-cicd-platform
```

The Terraform state and configuration for the ECR repository are
maintained under `terraform/ecr/`. The application has not yet been
deployed to AWS compute.

## ECR Image Tagging and Retention

CI images use the following naming convention:

``` text
git-<full-git-commit-sha>
```

Example:

``` text
git-bb9952a63021d2e339fa8eee929d840a5a7e78c8
```

The tag links a CI image to the commit that produced it.

An Amazon ECR lifecycle policy has been applied to retain the **10
newest images matching the `git-` tag prefix**. Older matching CI images
become eligible for expiration as new images are published. The initial
lifecycle preview reported zero expiring images and zero archiving
images.

The rule is scoped to the `git-` prefix and does not match the existing
`1.0.0` release tag, the older plain-SHA tag, or untagged images. ECR
lifecycle evaluation is asynchronous, so images selected for expiration
may not disappear immediately.

## Deployment

### Local Python deployment

Create and activate a virtual environment:

``` bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m app.main
```

The application listens on `http://localhost:5000`.

### Local Docker deployment

Build the image:

``` bash
docker build -t devsecops-cicd-platform:1.0.0 .
```

Run it:

``` bash
docker run -d \
  --name devsecops-platform \
  -p 5000:5000 \
  devsecops-cicd-platform:1.0.0
```

Check the container:

``` bash
docker ps
```

The container should report a healthy status after its health check
succeeds.

## Testing

The API test suite covers:

-   `/health`
-   `/api/v1/status`
-   `/api/v1/info`

Run tests:

``` bash
pytest
```

Generate a coverage report:

``` bash
pytest --cov=app
```

Previously recorded test evidence is three passing tests and 92%
coverage. Re-run the suite to confirm the current result.

### Container verification

Health endpoint:

``` bash
curl http://localhost:5000/health
```

Expected response:

``` json
{
  "service": "devsecops-cicd-platform",
  "status": "healthy"
}
```

Status endpoint:

``` bash
curl http://localhost:5000/api/v1/status
```

Expected response:

``` json
{
  "status": "operational",
  "version": "1.0.0"
}
```

Information endpoint:

``` bash
curl http://localhost:5000/api/v1/info
```

Expected response:

``` json
{
  "application": "DevSecOps CI/CD Platform",
  "environment": "development",
  "version": "1.0.0"
}
```

The container has previously been verified to run as `appuser`, with the
Docker health check reporting `healthy`. Gunicorn was observed starting
two workers in the container.

## Monitoring

Application monitoring and centralized observability have not yet been
implemented. Current basic operational checks include the `/health`
endpoint and Docker health status.

Planned improvements:

-   Application metrics
-   Structured logging
-   Monitoring and alerting
-   Centralized log collection

## Failure Recovery

Automated deployment recovery has not yet been implemented. Current
operational verification includes Docker health checks, the application
health endpoint, Gunicorn process logging, and container status
inspection.

Future work includes deployment recovery mechanisms, rollback
procedures, and infrastructure-level health monitoring.

## Project Structure

``` text
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
├── terraform/
│   └── ecr/
├── .dockerignore
├── .gitignore
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

This is a high-level representation; the repository may contain
additional files.

## Getting Started

### Prerequisites

-   Python 3.12+
-   Docker
-   Git

### Clone the repository

``` bash
git clone https://github.com/markfosu/devsecops-cicd-platform.git
cd devsecops-cicd-platform
```

### Run tests locally

``` bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

### Run with Docker

``` bash
docker build -t devsecops-cicd-platform:1.0.0 .
docker run -d \
  --name devsecops-platform \
  -p 5000:5000 \
  devsecops-cicd-platform:1.0.0
curl http://localhost:5000/health
```

## Lessons Learned

### Runtime reproducibility

Python virtual environments isolate local development dependencies,
while Docker provides a consistent application runtime.

### Production application serving

Flask's development server is useful during development, but the
container uses Gunicorn as the WSGI server.

### Container security

The application does not require root privileges, so the container runs
under the dedicated `appuser` account.

### Docker layer caching

Copying dependency files before application source code allows Docker to
reuse the dependency installation layer when application code changes.

### Health checks

A running container does not necessarily mean the application is
functioning correctly. The Docker health check verifies that `/health`
responds successfully.

### Continuous integration and security gates

Automated tests, dependency auditing, and container scanning provide
repeatable checks. Required jobs gate publication so an image is not
published through the normal CI path when those checks fail.

### Short-lived AWS credentials

OIDC lets GitHub Actions assume a restricted AWS role without storing
long-lived AWS access keys in GitHub secrets.

### Incremental engineering

Implementing and validating one stage before adding complexity reduces
troubleshooting scope and creates evidence for engineering decisions.

## Future Improvements

1.  Deploy the application to AWS compute after choosing and reviewing a
    cost-appropriate architecture.
2.  Add application and infrastructure monitoring.
3.  Implement structured logging, centralized log collection, and
    alerting.
4.  Develop deployment rollback and failure-recovery mechanisms.
5.  Add additional secrets-management controls where required.
6.  Introduce multi-environment deployment.
7.  Document operational runbooks and recovery procedures.
8.  Continue reviewing vulnerability findings and updating the container
    base image.
