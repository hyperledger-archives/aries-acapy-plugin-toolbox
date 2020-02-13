Aries Cloud Agent - Python Plugin for Aries Toolbox
===================================================

Quickstart Guide
----------------

Requirements:
- Python 3.6 or higher
- ACA-Py @ master

> **Note:** This plugin is currently compatible only with the master branch of
> ACA-Py. Once a release including the new plugin interface is published to
> PyPI, these instructions will be updated accordingly.

### Setup Aries Cloud Agent - Python

If you already have an existing installation of ACA-Py, you can skip these steps
and move on to [plugin installation](#plugin-installation). It is also worth
noting that this is not the only way to setup an ACA-Py instance. For more setup
configurations, see the [Aries Cloud Agent - Python
repository](https://github.com/hyperledger/aries-cloudagent-python).

First, clone
[ACA-Py](https://github.com/hyperledger/aries-cloudagent-python) and prepare a
virtual environment:
```sh
$ git clone https://github.com/hyperledger/aries-cloudagent-python
$ cd aries-cloudagent-python
$ python3 -m venv env
$ source env/bin/activate
```

Install ACA-Py into the virtual environment:
```sh
$ pip install -e .
```
**Or** include the `indy` feature if you want to use Indy ledgers or wallets:
```sh
$ pip install -e .[indy]
```

### Plugin Installation

Install this plugin into the virtual environment:
```sh
$ pip install git+https://github.com/hyperledger/aries-acapy-plugin-toolbox.git@master#egg=acapy-plugin-toolbox
```

### Plugin Loading
Start up ACA-Py with the plugin parameter:
```sh
$ aca-py start -it http localhost 3000 -ot http -e http://localhost:3000 --plugin acapy_plugin_toolbox
```

Passing the whole package `acapy_plugin_toolbox` will load all protocol
handlers. Individual modules and groups are also separately loadable.

Available modules include:
- `connections`: Handlers for the `admin-connections` protocol.
- `static_connections`: Handlers for the `admin-static-connections` protocol.
- `schema`: Handlers for the `admin-schemas` protocol.
- `credential_definitions`: Handlers for the `admin-credential-definitions`
  protocol.
- `dids`: Handlers for the `admin-dids` protocol.
- `holder`: Handlers for the `admin-holder` protocol.
- `issuer`: Handlers for the `admin-issuer` protocol.
- `basicmessage`: Handlers for the `admin_basicmessage` protocol.

> **Note:** Links to documentation for each of the above protocols will be added
> when they become available.

Available groups include:
- `all`: The default group loaded by the package, loading all handlers.
- `connections`: Handlers from `connections` and `static_connections`.
- `holder`: Handlers from `credential_definitions` and `holder`.
- `issuance`: Handlers from  `schema`, `credential_definitions`, `did`, and
  `issuer`.

#### Example
To load the "connections" group and the "basicmessage" module:
```sh
$ aca-py start \
	-it localhost 3000 \
	-ot http -e http://localhost:3000 \
	--plugin acapy_plugin_toolbox.group.connections
	--plugin acapy_plugin_toolbox.basicmessage
```

### Indy Startup Example
To use all the features of the toolbox, you'll need the `indy` feature installed
and a start up command similar to the following (with environment variables
replaced with your appropriate values or available in the environment):
```sh
$ aca-py start \
    -it http 0.0.0.0 3000 \
    -ot http \
    -e $ENDPOINT \
    --label $AGENT_NAME \
    --auto-accept-requests --auto-ping-connection \
    --auto-respond-credential-proposal --auto-respond-credential-offer --auto-respond-credential-request --auto-store-credential \
    --auto-respond-presentation-proposal --auto-respond-presentation-request --auto-verify-presentation \
    --invite --invite-role admin --invite-label "$AGENT_NAME (admin)" \
    --genesis-url https://raw.githubusercontent.com/sovrin-foundation/sovrin/master/sovrin/pool_transactions_sandbox_genesis \
    --wallet-type indy \
    --plugin acapy_plugin_toolbox
```

### Combined HTTP+WS Transport
This plugin also includes a side-loadable combined HTTP and WebSocket transport
that enables accepting both HTTP and WebSocket connections on the same port.
This is useful for running the agent behind a tunneling service such as ngrok
that generally provides only one port-to-port tunnel at a time.

To use the HTTP+WS transport:
```sh
$ aca-py start \
	-it acapy_plugin_toolbox.http_ws localhost 3000 \
	-ot http \
	-e http://localhost:3000 ws://localhost:3000
```

Note that you do not need to load any other plugins for this transport but you
can by specifying `--plugin` as shown in the examples above.
