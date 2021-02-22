FROM bcgovimages/aries-cloudagent:py36-1.15-0_0.6.0rc0

USER root
ADD acapy_plugin_toolbox aries-acapy-plugin-toolbox/acapy_plugin_toolbox
ADD requirements.txt aries-acapy-plugin-toolbox
ADD setup.py aries-acapy-plugin-toolbox
ADD README.md aries-acapy-plugin-toolbox
ADD docker/default.yml .
RUN chown -R indy:indy aries-acapy-plugin-toolbox
USER $user

RUN pip3 install -e ./aries-acapy-plugin-toolbox

ENTRYPOINT ["/bin/bash", "-c", "aca-py \"$@\"", "--"]
CMD ["start", "--plugin", "acapy_plugin_toolbox", "--arg-file", "default.yml"]
