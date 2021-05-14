FROM bcgovimages/von-image:py36-1.16-0

# Make ACA-Py Install location more accessible
RUN ln -s $(pyenv prefix)/lib/python3.6/site-packages site-packages

USER root
ADD acapy_plugin_toolbox acapy_plugin_toolbox
ADD requirements.txt .
ADD setup.py .
ADD README.md .
ADD docker/default.yml .
RUN chown -R indy:indy .
USER $user

RUN pip3 install -e .

ENTRYPOINT ["/bin/bash", "-c", "aca-py \"$@\"", "--"]
CMD ["start", "--plugin", "acapy_plugin_toolbox", "--arg-file", "default.yml"]
