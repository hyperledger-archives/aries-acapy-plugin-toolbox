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
$ pip install git+https://github.com/sovrin-foundation/aca-plugin-toolbox.git@master#egg=aca-plugin-toolbox
```

Start up ACA-Py with the plugin parameter:
```sh
$ aca-py start -it localhost 3000 -ot http -e http://localhost 3000 --plugin aca_plugin_toolbox
```

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
    --plugin aca_plugin_toolbox
```
