FROM python:3.7
WORKDIR /app

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | POETRY_HOME=/opt/poetry python - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock /app/

RUN poetry install --no-root

COPY ./echo.py /app/
ENTRYPOINT ["/bin/sh", "-c", "poetry run \"$@\"", "--"]
CMD python -m uvicorn echo:app --host 0.0.0.0 --port 80
