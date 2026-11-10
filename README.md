# DevSecOps CI/CD Platform

A Python Flask API project demonstrating secure software delivery
through automated testing, dependency auditing, secret detection,
container vulnerability scanning, Software Bill of Materials (SBOM)
generation, infrastructure-as-code security, and gated container
publishing to Amazon Elastic Container Registry (ECR).

## Overview

This project demonstrates an incremental approach to building a secure
CI/CD platform using modern DevSecOps practices.

The application runs locally in Docker, while GitHub Actions automates
application testing, dependency auditing, secret scanning, container
vulnerability assessment, SBOM generation, and gated image publishing to
Amazon ECR. Terraform manages the ECR repository, while GitHub Actions
uses AWS OpenID Connect (OIDC) for short-lived AWS credentials.

> **Current scope:** Application containerization, CI/CD automation,
> security validation, SBOM generation, Terraform validation, and
> container publishing to Amazon ECR are implemented. The application
> has not yet been deployed to AWS compute.

## Problem Statement

The goal is to demonstrate how an application can move from source code
to a tested, security-validated container image through repeatable
automation and least-privilege cloud access.

## Architecture

### Application delivery and CI/CD flow

``` text
Developer
    |
    v
GitHub Repository (push / pull request)
    |
    v
GitHub Actions CI Pipeline
    |
    +----------------------+----------------------+
    |                      |                      |
    v                      v                      v
  Test                Secret Scan          Container Scan
    |                      |                      |
    v                      v                      v
pytest                 Gitleaks                Trivy
pip-audit              Full Git History        Image Scan
    |                      |                      |
    +----------------------+----------------------+
                           |
                           v
                 All required jobs pass
                           |
                           v
                 Publish job (main only)
                           |
              +------------+-------------+
              |            |             |
              v            v             v
             Syft        AWS OIDC       Trivy
             SBOM        Authentication Final Scan
              |            |             |
              +------------+-------------+
                           |
                           v
                       Amazon ECR
                           |
                           v
                 Image digest verification
```

The publishing job depends on the successful completion of `test`,
`secret-scan`, and `container-scan`. Publishing is restricted to
qualifying pushes to `main`.

### Local application runtime

``` text
Flask API
    |
    v
Gunicorn WSGI Server
    |
    v
Docker Container
    +--> Non-root appuser
    +--> Container health check
    +--> localhost:5000
```

### Terraform validation flow

``` text
Terraform Configuration
        |
        v
GitHub Actions - Terraform CI
        |
        +--> Terraform fmt
        +--> Terraform init
        +--> Terraform validate
        +--> Checkov security scan
        |
        v
     Pass / Fail
```

Terraform CI runs independently of the application CI/CD workflow. It
validates Terraform configuration and performs infrastructure-as-code
security scanning without provisioning AWS infrastructure.

## Technology Stack

### Implemented

-   Python 3.12
-   Flask 3.1.3
-   Gunicorn 23.0.0
-   Docker
-   pytest and pytest-cov
-   pip-audit for Python dependency auditing
-   Gitleaks for secret detection
-   Trivy for container vulnerability scanning
-   Syft for SBOM generation
-   CycloneDX JSON SBOM format
-   Git and GitHub
-   GitHub Actions
-   Terraform
-   Checkov 3.4.3
-   Amazon Elastic Container Registry (ECR)
-   AWS IAM and GitHub Actions OIDC

### Planned

-   PostgreSQL database integration
-   Local Kubernetes deployment
-   Application and infrastructure monitoring
-   Centralized logging and alerting
-   Automated deployment rollback and recovery
-   Multi-environment deployment
-   GitOps-based deployment automation

## CI/CD Pipeline

The application workflow is defined in `.github/workflows/ci.yml` and
runs on pushes to `main` and pull requests targeting `main`.

### 1. Application testing and dependency auditing

The `test` job:

1.  Checks out the repository.
2.  Sets up Python 3.12.
3.  Installs application and development dependencies.
4.  Audits production dependencies using `pip-audit`.
5.  Runs pytest and generates a coverage report.

### 2. Secret scanning

Gitleaks identifies accidentally committed credentials and sensitive
information.

The secret-scanning job:

-   Checks out the full Git history using `fetch-depth: 0`.
-   Installs a pinned Gitleaks version.
-   Verifies the downloaded release using its SHA256 checksum.
-   Scans the repository's Git history.
-   Generates a SARIF security report.
-   Uploads the report as a GitHub Actions artifact.

The scan uses:

``` bash
gitleaks git . \
  --redact \
  --exit-code 1 \
  --report-format sarif \
  --report-path gitleaks-report.sarif
```

The pipeline fails when Gitleaks detects a matching secret. Deleting a
credential from the current working tree does not remove it from
previous Git commits.

### 3. Container vulnerability scanning

The `container-scan` job builds the Docker image and scans operating
system and library vulnerabilities using Trivy.

The scan is configured to fail on matching High and Critical
vulnerabilities with available fixes. The `ignore-unfixed: true` setting
excludes findings for which Trivy does not identify an available fix; it
does not mean excluded vulnerabilities are harmless.

### 4. SBOM generation

Syft generates a Software Bill of Materials for the locally built
container image.

-   Format: CycloneDX JSON.
-   The SBOM describes the image intended for publication.
-   The SBOM is uploaded as a GitHub Actions artifact.
-   Artifact retention is configured for 30 days.

Example command:

``` bash
syft <image-reference> \
  -o cyclonedx-json \
  > sbom.cdx.json
```

The SBOM provides visibility into the software components included in
the container image and supports software supply-chain transparency.

### 5. Gated image publishing

The publishing job depends on:

-   `test`
-   `secret-scan`
-   `container-scan`

It runs only for qualifying pushes to `main`.

The publishing process:

1.  Builds the image using a commit-specific tag.
2.  Generates the CycloneDX SBOM.
3.  Performs the publishing-stage Trivy scan.
4.  Authenticates to AWS using GitHub Actions OIDC.
5.  Logs in to Amazon ECR.
6.  Pushes the image to the private ECR repository.
7.  Retrieves the image digest from ECR.
8.  Compares the ECR digest with the digest associated with the locally
    built image.

This verifies that the image published to ECR corresponds to the image
produced by the CI build.

### CI validation and failure-gate testing

The pipeline has been tested with deliberately introduced failures to
verify that publishing is blocked when required checks fail.

**Application test failure**

An intentionally incorrect expected HTTP status code was introduced into
a test. The pytest job failed, independent validation jobs continued,
and the publishing job was skipped. After correcting the assertion, the
workflow returned to a passing state.

**Secret detection failure**

A synthetic test credential was introduced in a temporary test branch.
Gitleaks detected it, the secret-scanning job failed with exit code `1`,
and publishing was skipped. The test credential was subsequently removed
from Git history, the temporary branch was cleaned up, and the secret
scan passed.

These tests demonstrate that application and security validation stages
act as publishing gates.

## Terraform CI and Infrastructure Security

The project includes a separate Terraform CI workflow defined in
`.github/workflows/terraform-ci.yml`.

The workflow is triggered by:

-   Pushes to `main` affecting Terraform files or the Terraform CI
    workflow.
-   Pull requests targeting `main` affecting Terraform files or the
    Terraform CI workflow.
-   Manual execution through GitHub Actions.

### Terraform validation stages

The workflow performs:

1.  Repository checkout.
2.  Terraform CLI setup.
3.  Formatting validation using `terraform fmt -check -recursive`.
4.  Initialization using `terraform init -backend=false -input=false`.
5.  Configuration validation using `terraform validate`.

### Infrastructure-as-Code security scanning

Checkov identifies security misconfigurations and policy violations.

``` bash
checkov -d . --framework terraform
```

Checkov is pinned to version `3.4.3`.

### Current Checkov assessment

  -----------------------------------------------------------------------
  Check ID                Security control        Result
  ----------------------- ----------------------- -----------------------
  `CKV_AWS_41`            No hard-coded AWS       Passed
                          credentials

  `CKV_AWS_163`           ECR image scanning on   Passed
                          push

  `CKV_AWS_51`            Immutable ECR image     Passed
                          tags

  `CKV_AWS_136`           ECR encryption using    Skipped with documented
                          KMS                     exception
  -----------------------------------------------------------------------

The repository uses AWS-managed AES-256 encryption at rest. The
KMS-specific Checkov policy is intentionally skipped because the project
does not require customer-managed KMS keys. This is a documented policy
exception, not an absence of encryption.

### Terraform CI security boundary

Terraform CI performs static configuration validation and security
scanning. It does not authenticate to AWS, execute `terraform plan` or
`terraform apply`, or provision AWS resources.

## Security

### Application and container security controls

-   Dedicated non-root container user (`appuser`).
-   Separation of production and development dependencies.
-   `.dockerignore` to limit the Docker build context.
-   Docker health checks.
-   Python slim runtime image.
-   Operating system package updates during image build.
-   Removal of `pip` from the runtime image after dependency
    installation.
-   `pip-audit` dependency vulnerability auditing.
-   Gitleaks secret detection across Git history.
-   Trivy container vulnerability scanning.
-   Checkov Terraform security scanning.
-   Documented Terraform security exceptions.

### Container vulnerability assessment

An earlier local Trivy assessment of `devsecops-cicd-platform:1.0.5`
reported:

-   **Unfiltered scan:** 44 High-severity findings and 0 Critical
    findings against Debian 13.7.
-   **Python packages:** No High or Critical findings in the scanned
    Python package metadata.
-   **Filtered scan:** No High or Critical findings with
    `--ignore-unfixed`.

The unfiltered findings included repeated package-level reports for some
CVEs. These results do not establish that the image is
vulnerability-free. Operating system findings should be reassessed as
base-image and package security updates become available.

### AWS authentication and permissions

GitHub Actions assumes a dedicated AWS IAM role using OIDC rather than
storing long-lived AWS access keys in GitHub repository secrets.

The trust policy restricts the intended GitHub repository and `main`
branch. The IAM role's ECR permissions are scoped to the target
repository and required publishing operations, including image
publishing and digest verification.

## Infrastructure

Terraform manages the private Amazon ECR repository.

Configured controls include:

-   Immutable image tags.
-   Image scanning on push.
-   AES-256 encryption at rest.
-   Lifecycle policy retaining the 10 newest CI images tagged with the
    `git-` prefix.

ECR repository:

``` text
095453158828.dkr.ecr.us-east-1.amazonaws.com/devsecops-cicd-platform
```

Terraform configuration is maintained under `terraform/ecr/`. The
application has not yet been deployed to AWS compute.

## ECR Image Tagging and Retention

CI images use the following naming convention:

``` text
git-<full-git-commit-sha>
```

Example:

``` text
git-bb9952a63021d2e339fa8eee929d840a5a7e78c8
```

The tag links each published CI image to the Git commit that produced
it.

The ECR lifecycle policy retains the 10 newest images matching the
`git-` prefix. The lifecycle rule does not match the existing `1.0.0`
release tag, older plain-SHA tags, or untagged images.

ECR lifecycle evaluation is asynchronous, so images selected for
expiration may not disappear immediately.

### Image digest verification

After publishing, the workflow retrieves the image digest from ECR and
compares it with the digest associated with the locally built image.
This provides an additional verification step beyond confirming that the
image push command completed successfully.

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

Previously recorded results:

-   3 passing tests.
-   92% test coverage.
-   Python 3.12.

### Container verification

**Health endpoint**

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

**Status endpoint**

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

**Information endpoint**

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
Docker health check reporting `healthy`.

## Monitoring

Application monitoring and centralized observability have not yet been
implemented.

Current basic operational checks include:

-   `/health` endpoint.
-   Docker health status.
-   Gunicorn process logging.
-   Container status inspection.

Planned improvements:

-   Application metrics.
-   Structured logging.
-   Monitoring and alerting.
-   Centralized log collection.

## Failure Recovery

Automated deployment recovery has not yet been implemented.

Current operational verification includes Docker health checks,
application health endpoints, Gunicorn process logging, and container
status inspection.

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
│       ├── ci.yml
│       └── terraform-ci.yml
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

This is a high-level representation. The repository may contain
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

Automated application tests, dependency auditing, secret detection, and
container scanning provide repeatable validation. Required jobs gate
publishing so an image is not published through the normal CI path when
a required check fails.

### Secret detection and Git history

Deleting a sensitive file from the current working tree does not remove
it from previous Git commits. Full-history scanning helps identify
historical exposure. When a credential is committed, remediation may
require removing it from Git history and coordinating the resulting
history rewrite.

### Software supply-chain transparency

Generating a CycloneDX SBOM with Syft provides visibility into the
software components included in the container image.

### Image integrity

Comparing the locally built image digest with the ECR digest adds an
integrity verification step to the publishing workflow.

### Short-lived AWS credentials

OIDC lets GitHub Actions assume a restricted AWS role without storing
long-lived AWS access keys in GitHub secrets.

### Infrastructure-as-Code security

Terraform validation confirms that configuration is syntactically valid,
but does not guarantee that the configuration follows security best
practices. Checkov adds policy-based security checks.

### Security policy exceptions

A security scanner finding must be evaluated in context. The ECR
repository uses AES-256 encryption at rest, so the KMS-specific Checkov
requirement is documented as an intentional exception.

### Incremental engineering

Implementing and validating one stage before adding complexity reduces
troubleshooting scope and creates evidence for engineering decisions.

## Future Improvements

1.  Integrate PostgreSQL into the Flask application.
2.  Introduce local Kubernetes deployment using Minikube or kind.
3.  Add application and infrastructure monitoring.
4.  Implement structured logging, centralized log collection, and
    alerting.
5.  Develop deployment rollback and failure-recovery mechanisms.
6.  Deploy the application to AWS compute after reviewing a
    cost-appropriate architecture.
7.  Introduce GitOps-based deployment automation.
8.  Add multi-environment deployment.
9.  Document operational runbooks and recovery procedures.
10. Continue reviewing vulnerability findings and updating the container
    base image.
