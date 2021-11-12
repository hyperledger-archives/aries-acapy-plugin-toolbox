Aries Cloud Agent - Python Plugin for Aries Toolbox
===================================================

## ACA-Py Version Compatibility

To avoid a confusing pseudo-lock-step release, this plugin is
versioned independent of ACA-Py. Plugin releases will follow standard
[semver](semver.org) but each release will also be tagged with a mapping to an
ACA-Py version with the format `acapy-X.Y.Z-J` where `X.Y.Z` corresponds to the
ACA-Py version supported and `J` is an incrementing number for each new plugin
release that targets the same version of ACA-Py.

You should look for the most recent release tagged with the version of ACA-Py
you are using (with the highest value for `J`).

## Quickstart Guide - Docker Demos

To quickly run a number of different scenarios, [check out the demo
instructions](demo/README.md).

## Quickstart Guide - Development-friendly Docker

For a developer friendly docker container with ACA-Py and the toolbox installed
and reasonable defaults, [checkout the docker instructions](docker/README.md).

## Installation

Requirements:
- Python 3.6 or higher
- ACA-Py

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
Note: If you are using the `indy` feature, you will need to have the indy-sdk
library installed. If it's not installed, please see
[Installing the SDK](https://github.com/hyperledger/indy-sdk/blob/master/README.md#installing-the-sdk)

### Plugin Installation

Install this plugin into the virtual environment:

```sh
$ pip install git+https://github.com/hyperledger/aries-acapy-plugin-toolbox.git@main#egg=acapy_plugin_toolbox
```

**Note:** Depending on your version of `pip`, you may need to drop the
`#egg=...` to install the plugin with the above command.

### Plugin Loading
Start up ACA-Py with the plugin parameter:
```sh
$ aca-py start \
    -it http localhost 3000 -it ws localhost 3001 \
    -ot http \
    -e http://localhost:3000 ws://localhost:3001 \
    --plugin acapy_plugin_toolbox
```

Alternatively, you may use the demo configs in `demo/configs` to startup ACA-Py
similarly to the demos. These demos automatically set many options, such as
ports, config options, plugins to load, etc. To do so, copy one of the config
files to the current directory and run the following command, substituting
`./{config}.yml` with the config file you have chosen:
```
aca-py start --arg-file ./{config}.yml
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
    --connections-invite --invite-label "My agent admin connection" \
	--invite-metadata-json '{"group": "admin"}'
```

The invitation will be printed to the screen after the agent has started up and
can then be pasted into the toolbox.

#### Groups

This plugin adds metadata to connections to distinguish between "admin
privileged" connections and connections that are not allowed to execute "admin"
operations. The `invite-metadata-json` flag adds this metadata to the connection
created on startup. Within the toolbox, you can create more invitations with the
"admin" group and use these invitations on other devices or individuals which
are authorized to perform administrative tasks.

### Using Indy Verifiable Credentials

To use all the features of the toolbox, you'll need the `indy` feature installed
(as described in [Setup Aries Cloud Agent -
Python](#setup-aries-cloud-agent-python)). [Check out the demo configurations
for Alice or Bob](demo/configs/alice.yml) for a configuration using the Sovrin
BuilderNet and some reasonable defaults.

### Combined HTTP+WS Transport
This plugin includes a side-loadable combined HTTP and WebSocket transport
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

## License

[Apache License Version 2.0](https://github.com/hyperledger/aries-acapy-plugin-toolbox/blob/main/LICENSE)
