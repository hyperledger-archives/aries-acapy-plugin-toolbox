aca-py start \
    -it acapy_plugin_toolbox.http_ws 0.0.0.0 "$PORT" \
    -ot http \
    -e "$ENDPOINT" "${ENDPOINT/http/ws}" \
    --label "$AGENT_NAME" \
    --auto-accept-requests --auto-ping-connection \
    --auto-respond-credential-proposal --auto-respond-credential-offer --auto-respond-credential-request --auto-store-credential \
    --auto-respond-presentation-proposal --auto-respond-presentation-request --auto-verify-presentation \
    --preserve-exchange-records \
    --invite --invite-role admin --invite-label "$AGENT_NAME (admin)" \
    --genesis-url https://raw.githubusercontent.com/sovrin-foundation/sovrin/master/sovrin/pool_transactions_sandbox_genesis \
    --wallet-type indy \
    --plugin acapy_plugin_toolbox \
    --admin 0.0.0.0 $ADMIN_PORT --admin-insecure-mode \
    --debug-connections \
    --debug-credentials \
    --debug-presentations \
    --enable-undelivered-queue \
    "$@"
