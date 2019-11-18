FROM bcgovimages/von-image:py36-1.11-1
# 77f4.... should be changed to a supported tag when there is one.
RUN pip3 install git+https://github.com/hyperledger/aries-cloudagent-python.git@77f47b7f3d47bad89f6177f4e95b8a50abc38b5d#egg=aries-cloudagent[indy]
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
