# BERDL JupyterHub on Kubernetes

BERDL JupyterHub is a Python application that provides a customized JupyterHub deployment for Kubernetes. It uses KubeSpawner to launch user notebook servers as individual Kubernetes pods and authenticates users against KBase. The application integrates with Spark cluster management, MinIO object storage, and governance APIs.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

- Bootstrap, build, and test the repository:
  - Install uv package manager: `pip install uv` (if not available)
  - `uv sync --locked --inexact` -- installs all dependencies including dev tools. Takes ~40 seconds. NEVER CANCEL. Set timeout to 120+ seconds.
  - `uv run pytest` -- runs 33 unit tests. Takes ~1 second. NEVER CANCEL. Set timeout to 60+ seconds.
- Lint and format code:
  - `uv run ruff check .` -- checks code style. Takes <1 second. NEVER CANCEL. Set timeout to 30+ seconds.
  - `uv run ruff format --check .` -- checks formatting. Takes <1 second. NEVER CANCEL. Set timeout to 30+ seconds.
  - `uv run ruff format .` -- formats code. Takes <1 second. NEVER CANCEL. Set timeout to 30+ seconds.
  - `uv run ruff check . --fix` -- fixes linting issues automatically. Takes <1 second. NEVER CANCEL. Set timeout to 30+ seconds.
- Build Docker image:
  - `docker build -t berdl-jupyterhub .` -- builds container image. WARNING: May fail in sandboxed environments due to SSL certificate issues when installing uv. Takes 2-5 minutes in normal environments. NEVER CANCEL. Set timeout to 600+ seconds.
- Deploy to local Kubernetes:
  - `kubectl apply -k local_dev/` -- deploys using pre-built images. Takes 10-30 seconds. NEVER CANCEL. Set timeout to 120+ seconds.
  - `kustomize build local_dev/` -- generates Kubernetes manifests. Takes ~2 seconds. NEVER CANCEL. Set timeout to 60+ seconds.

## Validation

- ALWAYS run through the complete test suite after making changes: `uv run pytest`
- Test specific modules: `uv run pytest unit_tests/api_utils/` or `uv run pytest -k "governance"`
- Test with reduced output: `uv run pytest -q` for quieter output
- Stop on first failure: `uv run pytest -x` for faster feedback during development
- ALWAYS run linting before committing: `uv run ruff check . && uv run ruff format --check .`
- ALWAYS test Kubernetes manifest generation: `kustomize build local_dev/`
- You cannot fully test the JupyterHub application without a Kubernetes cluster and external service dependencies (KBase auth, MinIO, Spark manager, etc.)
- The CI pipeline (.github/workflows/test.yml) will fail if code is not properly formatted or linted

## Validation Scenarios

After making code changes, test these scenarios:
- **Unit tests**: Run `uv run pytest` to ensure all 33 tests pass
- **Code quality**: Run `uv run ruff check . && uv run ruff format --check .` to ensure proper formatting
- **Configuration validation**: Test that configuration loads without errors by importing config modules
- **Kubernetes manifests**: Run `kustomize build local_dev/` to verify YAML generation works
- **Docker build**: Attempt `docker build -t berdl-jupyterhub .` if in an environment with internet access

## Common Tasks

### Prerequisites
- Python 3.10 or higher (project uses .python-version file specifying 3.10)
- uv package manager
- Docker (for container builds)
- kubectl and kustomize (for Kubernetes deployment)

### Repository Structure
```
.
├── .github/workflows/     # CI/CD pipelines
├── berdlhub/             # Main application code
│   ├── api_utils/        # External API integrations (Spark, Governance)
│   ├── auth/             # KBase authentication modules
│   └── config/           # JupyterHub configuration modules
├── local_dev/            # Kubernetes manifests for local development
├── unit_tests/           # Test suite
├── Dockerfile            # Container image definition
├── pyproject.toml        # Python project configuration and dependencies
└── uv.lock              # Locked dependency versions
```

### Key Configuration Files
- `berdlhub/config/0-jupyterhub_config.py` -- Main configuration orchestrator
- `berdlhub/config/hooks.py` -- Kubernetes pod lifecycle hooks
- `berdlhub/config/spawner.py` -- KubeSpawner configuration
- `berdlhub/config/auth.py` -- KBase authentication setup
- `local_dev/configmap.yaml` -- Environment variables for local development
- `local_dev/hub.yaml` -- Kubernetes deployment configuration

### Environment Variables (Required for Runtime)
Core variables needed for the application to function:
- `JUPYTERHUB_COOKIE_SECRET_64_HEX_CHARS` -- Session security
- `KBASE_AUTH_URL` -- KBase authentication service
- `KBASE_ORIGIN` -- KBase service URL
- `CDM_TASK_SERVICE_URL` -- CTS service URL
- `GOVERNANCE_API_URL` -- Governance API URL
- `MINIO_ENDPOINT_URL` -- Object storage URL
- `SPARK_CLUSTER_MANAGER_API_URL` -- Spark management URL
- `BERDL_NOTEBOOK_IMAGE_TAG` -- User notebook container image

### CI/CD Pipeline
- `.github/workflows/test.yml` -- Runs tests, linting, and formatting checks on PRs
- `.github/workflows/docker-publish.yaml` -- Builds and publishes container images

### Development Workflow
1. Make code changes
2. Run tests: `uv run pytest`
3. Check linting: `uv run ruff check . && uv run ruff format --check .`
4. Fix any issues: `uv run ruff check . --fix && uv run ruff format .`
5. Test Kubernetes manifests: `kustomize build local_dev/`
6. Commit changes (CI will validate)

### Known Limitations
- Docker builds may fail in sandboxed environments due to SSL certificate verification issues
- Full application testing requires external services (KBase, MinIO, Spark manager)
- Local Kubernetes deployment requires pre-configured node selector hostnames
- The application requires specific environment variables to start successfully

### Troubleshooting
- If `uv sync` fails, ensure Python 3.10+ is available
- If Docker build fails with SSL errors, this is expected in restricted network environments
- If tests fail, check that no external dependencies are assumed
- If linting fails, run `uv run ruff check . --fix` to auto-fix issues
- Always use `uv run python` instead of plain `python` to ensure dependencies are available
- Module imports may fail outside of `uv run` context due to git dependencies
- Always ensure the virtual environment is activated when running uv commands

### Testing Integration Points
The application integrates with several external services. When making changes:
- **Spark integration**: Test `berdlhub/api_utils/spark_utils.py` and related tests
- **Governance API**: Test `berdlhub/api_utils/governance_utils.py` and related tests
- **KBase authentication**: Test auth modules in `berdlhub/auth/`
- **Kubernetes spawning**: Test spawner configuration in `berdlhub/config/spawner.py`

### Performance Expectations
- Dependency installation: ~40 seconds
- Test suite execution: ~1 second (33 tests)
- Code formatting: <1 second
- Linting: <1 second
- Kubernetes manifest generation: ~2 seconds
- Docker image build: 2-5 minutes (when network accessible)

NEVER CANCEL long-running operations. Set appropriate timeouts and wait for completion.

## Common Tasks Reference

The following are outputs from frequently run commands. Reference them instead of viewing, searching, or running bash commands to save time.

### Repository Root Structure
```
.
├── .github/
│   ├── workflows/
│   │   ├── test.yml              # CI: tests, linting, formatting
│   │   └── docker-publish.yaml   # CI: container image builds
│   └── copilot-instructions.md   # This file
├── berdlhub/                     # Main application source
│   ├── api_utils/                # External service integrations
│   ├── auth/                     # KBase authentication modules
│   └── config/                   # JupyterHub configuration
├── local_dev/                    # Kubernetes development manifests
├── unit_tests/                   # Test suite (33 tests)
├── .python-version               # Python 3.10
├── Dockerfile                    # Container image definition
├── pyproject.toml               # Dependencies and project config
├── uv.lock                      # Dependency lock file
└── README.md                    # Basic documentation
```

### Key Environment Variables (Local Development)
From `local_dev/configmap.yaml`:
```
BERDL_SKIP_SPAWN_HOOKS=True                                    # Disables external service hooks
NODE_SELECTOR_HOSTNAME=lima-rancher-desktop                    # Kubernetes node selector
BERDL_NOTEBOOK_IMAGE_TAG=ghcr.io/bio-boris/berdl_notebook:main # User notebook image
KBASE_AUTH_URL=https://narrative.kbase.us/services/auth/       # Authentication service
GOVERNANCE_API_URL=http://minio-service:8000                   # Governance API endpoint
SPARK_CLUSTER_MANAGER_API_URL=http://sparkmanagerapi:8000      # Spark management API
```

### Test Command Variations
```bash
uv run pytest                    # All 33 tests (~1 second)
uv run pytest unit_tests/api_utils/  # API utility tests only
uv run pytest -k "governance"    # Tests matching pattern
uv run pytest -q                 # Quiet output mode
uv run pytest -x                 # Stop on first failure
```