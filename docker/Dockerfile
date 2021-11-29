FROM bcgovimages/von-image:py36-1.16-0 AS base

# Install and Configure Poetry
USER root
ENV POETRY_VERSION=1.1.11
ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://install.python-poetry.org | python -

ENV PATH="/opt/poetry/bin:$PATH"
RUN poetry config virtualenvs.in-project true

# Setup project
RUN mkdir acapy_plugin_toolbox && touch acapy_plugin_toolbox/__init__.py
COPY --chown=indy:indy pyproject.toml poetry.lock README.md ./
RUN poetry install --no-dev

FROM bcgovimages/von-image:py36-1.16-0
COPY --from=base --chown=indy:indy /home/indy/.venv /home/indy/.venv
ENV PATH="/home/indy/.venv/bin:$PATH"

COPY docker/default.yml ./
COPY acapy_plugin_toolbox acapy_plugin_toolbox
ENTRYPOINT ["/bin/bash", "-c", "aca-py \"$@\"", "--"]
CMD ["start", "--arg-file", "default.yml"]
