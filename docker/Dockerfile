FROM bcgovimages/von-image:py36-1.16-0

RUN pip3 install --no-cache-dir poetry

COPY acapy_plugin_toolbox acapy_plugin_toolbox
COPY pyproject.toml .
COPY poetry.lock .
COPY README.md .
COPY docker/default.yml .
USER root
RUN chown indy:indy -R .
USER indy

RUN poetry install --no-dev

# Make site packages location more accessible (for use with volumes)
RUN ln -s $(poetry env info -p)/lib/python3.6/site-packages site-packages

ENTRYPOINT ["/bin/bash", "-c", "poetry run aca-py \"$@\"", "--"]
CMD ["start", "--plugin", "acapy_plugin_toolbox", "--arg-file", "default.yml"]
