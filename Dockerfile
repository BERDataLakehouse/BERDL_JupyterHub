# Set the base image
FROM jupyterhub/jupyterhub:5.3.0

# Upgrade Node.js to fix configurable-http-proxy compatibility
RUN apt-get update && apt-get install -y curl git && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g configurable-http-proxy

# --- Environment Configuration ---
# Define variables for all key paths
ENV HUB_DIR=/hub
ENV BERDL_DIR=${HUB_DIR}/berdlhub
ENV PYTHONPATH=${HUB_DIR}
ENV JUPYTERHUB_TEMPLATES_DIR=${BERDL_DIR}/auth/templates


# --- Build Steps ---
WORKDIR ${HUB_DIR}
COPY pyproject.toml uv.lock .python-version ./
ENV UV_SYSTEM_PYTHON=1
RUN pip install uv && uv sync --locked --inexact --no-dev
RUN uv pip install --system .

COPY ./berdlhub/ ${BERDL_DIR}/

# This default directory must be mounted in order to preserve the sqlite and pid files
WORKDIR /srv/jupyterhub
ENTRYPOINT ["uv", "run"]
CMD ["jupyterhub", "-f", "/hub/berdlhub/config/0-jupyterhub_config.py"]