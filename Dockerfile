FROM bcgovimages/von-image:py36-1.14-0
RUN pip3 install git+https://github.com/sovrin-foundation/aries-cloudagent-python.git@8ba3f23#egg=aries-cloudagent[indy]

ADD . .

USER root
RUN pip3 install --no-cache-dir -e .

ADD https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64 ./jq
RUN chmod +x ./jq
COPY startup.sh startup.sh
RUN chmod +x ./startup.sh
COPY ngrok-wait.sh wait.sh
RUN chmod +x ./wait.sh

USER $user

CMD ./wait.sh ./startup.sh
