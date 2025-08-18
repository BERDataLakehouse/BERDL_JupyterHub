# Set the base image
FROM jupyterhub/jupyterhub:5.3.0

# Required for installing python packages from git
RUN apt-get update && apt-get install -y git

# --- Environment Configuration ---
# Define variables for all key paths
ENV HUB_DIR=/hub
ENV BERDL_DIR=${HUB_DIR}/berdlhub
ENV PYTHONPATH=${HUB_DIR}
ENV JUPYTERHUB_TEMPLATES_DIR=${BERDL_DIR}/auth/templates


# --- Build Steps ---
WORKDIR ${HUB_DIR}
COPY pyproject.toml uv.lock .python-version ./
RUN pip install uv && uv sync --locked --inexact --no-dev

COPY ./berdlhub/ ${BERDL_DIR}/


# This default directory must be mounted in order to preserve the sqlite and pid files
WORKDIR /srv/jupyterhub
ENTRYPOINT ["jupyterhub"]
CMD ["-f", "/hub/berdlhub/config/0-jupyterhub_config.py"]