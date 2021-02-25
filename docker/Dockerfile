FROM bcgovimages/aries-cloudagent:py36-1.15-0_0.6.0rc0

ARG ACAPY=""
RUN if [ -n "${ACAPY}" ]; then pip3 install ${ACAPY}; fi

ADD acapy_plugin_toolbox aries-acapy-plugin-toolbox/acapy_plugin_toolbox
ADD requirements.txt aries-acapy-plugin-toolbox
ADD setup.py aries-acapy-plugin-toolbox
ADD README.md aries-acapy-plugin-toolbox

USER root
RUN chown -R indy:indy aries-acapy-plugin-toolbox
USER $user

# Make ACA-Py Install location more accessible
RUN ln -s /home/indy/.pyenv/versions/3.6.9/lib/python3.6/site-packages site-packages

RUN pip3 install -e ./aries-acapy-plugin-toolbox

ADD docker/default.yml .

ENTRYPOINT ["/bin/bash", "-c", "aca-py \"$@\"", "--"]
CMD ["start", "--plugin", "acapy_plugin_toolbox", "--arg-file", "default.yml"]
