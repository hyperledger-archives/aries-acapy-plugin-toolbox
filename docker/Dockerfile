FROM python:3.7-slim AS base
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y curl

# Install and Configure Poetry
ENV POETRY_VERSION=1.3.2
ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://install.python-poetry.org | python -

ENV PATH="/opt/poetry/bin:$PATH"
RUN poetry config virtualenvs.in-project true

# Setup project
RUN mkdir acapy_plugin_toolbox && touch acapy_plugin_toolbox/__init__.py
COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --no-dev

FROM python:3.7-slim
WORKDIR /usr/src/app
COPY --from=base /usr/src/app/.venv /usr/src/app/.venv
ENV PATH="/usr/src/app/.venv/bin:$PATH"

COPY docker/default.yml ./
COPY acapy_plugin_toolbox acapy_plugin_toolbox
ENTRYPOINT ["/bin/bash", "-c", "aca-py \"$@\"", "--"]
CMD ["start", "--arg-file", "default.yml"]
