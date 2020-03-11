Aries Cloud Agent - Python Plugin for Aries Toolbox
===================================================

Quickstart Guide - Docker demo
------------------------------

Included in this repository are two Docker Compose files that can be used to
quickly experiment with the ACA-Py toolbox plugin and the Aries Toolbox. One
provides a single agent and the other two agents. In both cases, the resulting
agents are fully prepared to interact with other agents and the Sovrin Staging
Net for Verifiable Credentials exchange.

Requirements:
- Docker
- Docker Compose

### Disclaimer regarding the use of ngrok
Both compose setups use the ngrok tunneling service to make your agent available
to the outside world. One caveat of this, however, is that connections made from
your docker agent will expire within 8 hours as a limitation of the ngrok
free-tier. Therefore, **these setups are intended for demonstration purposes
only** and should not be relied upon as is for production environments.

### One Agent demo
To start the single agent demo:

```sh
$ docker-compose -f docker-compose.yml up --build
```

This will start two containers, one for the ngrok tunnel and one for the agent.
The agent container will wait until the ngrok endpoint is available before
starting up. The agent container will emit a fair amount of logs, including
`Node is not a validator` errors that can be safely ignored. At the end
of starting up it will print an invitation to the screen that can then be pasted
into the toolbox to connect to and remotely administer your docker agent.

### Two Agent demo
To start up an Alice and Bob demo:

```sh
$ docker-compose -f docker-compose_alice_bob.yml up --build
```

This will start four containers, two ngrok tunnels and two agent containers. Two
invitations will be printed to the screen corresponding to Alice and Bob.
Pasting these invitations into the toolbox will result in "Alice (Admin)" and
"Bob (Admin)" connections. Using the toolbox, you can then cause these two
agents to interact with each other in various ways.


Quickstart Guide - Running locally
----------------------------------

Requirements:
- Python 3.6 or higher
- ACA-Py @ master

> **Note:** This plugin is currently compatible only with the master branch of
> ACA-Py. Once a release including the new plugin interface is published to
> PyPI, these instructions will be updated accordingly.

> TODO: Add instructions for payment plugin loading

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
$ aca-py start \
	-it http localhost 3000 -it ws localhost 3001 \
	-ot http \
	-e http://localhost:3000 ws://localhost:3001 \
	--plugin acapy_plugin_toolbox
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
	-it http localhost 3000 -it ws localhost 3001 \
	-ot http \
	-e http://localhost:3000 ws://localhost:3001 \
	--plugin acapy_plugin_toolbox.group.connections
	--plugin acapy_plugin_toolbox.basicmessage
```

### Generating an invitation for use with the Toolbox
By default, ACA-Py has no preexisting connections. To have our agent interact
with other agents, we use the Aries Toolbox which is itself a simplified kind of
agent. We need ACA-Py to emit an invitation for the toolbox to begin the
connection process and bootstrap other interactions. To create an invitation that
can then be loaded into the Aries Toolbox:

```sh
$ aca-py start \
	-it http localhost 3000 -it ws localhost 3001 \
	-ot http \
	-e http://localhost:3000 ws://localhost:3001 \
	--plugin acapy_plugin_toolbox \
	--invite --invite-label "My agent admin connection" --invite-role admin
```

The invitation will be printed to the screen after the agent has started up and
can then be pasted into the toolbox.

#### Connection Roles

This plugin takes advantage of the concept of "roles" as built in to Aries Cloud
Agent - Python. Currently, this is a simple string stored along with other
connection details. In order to access the "admin" protocols, the originating
connection of the message must have a role of "admin." In the example above and
in the docker demos, `--invite` is used to generate an invitation at startup and
`--invite-role admin` causes the connection resulting from that invitation to
have the role of `admin`. Using the toolbox, you can create more invitations
with the "admin" role and use these invitations on other devices or given to
others with administrative privileges on your agent.

### Indy Startup Example
To use all the features of the toolbox, you'll need the `indy` feature installed
and a start up command similar to the following (with environment variables
replaced with your appropriate values or available in the environment):
```sh
$ aca-py start \
	-it http localhost 3000 -it ws localhost 3001 \
	-ot http \
    -e $ENDPOINT ${ENDPOINT/http/ws} \
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
