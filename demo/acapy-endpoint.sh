#!/bin/bash
ACAPY_ENDPOINT="$(./wait.sh)"
export ACAPY_ENDPOINT="[$ACAPY_ENDPOINT, ${ACAPY_ENDPOINT/http/ws}]"
exec "$@"
