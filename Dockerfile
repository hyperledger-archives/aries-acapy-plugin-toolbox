FROM bcgovimages/von-image:py36-1.11-1

COPY ./aries-cloudagent-python/requirements*.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt -r requirements.dev.txt

ADD ./aries-cloudagent-python/aries_cloudagent ./aries_cloudagent
ADD ./aries-cloudagent-python/bin ./bin
ADD ./aries-cloudagent-python/README.md ./README.md
ADD ./aries-cloudagent-python/setup.py ./setup.py

RUN pip3 install --no-cache-dir -e .[indy]
RUN pip3 install git+https://github.com/sovrin-foundation/aca-plugin-toolbox.git@master#egg=aca-plugin-toolbox

USER root
ADD https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64 ./jq
RUN chmod +x ./jq
COPY startup.sh startup.sh
RUN chmod +x ./startup.sh
COPY ngrok-wait.sh wait.sh
RUN chmod +x ./wait.sh

USER $user

CMD ./wait.sh ./startup.sh
