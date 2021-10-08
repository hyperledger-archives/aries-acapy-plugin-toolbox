Aries Cloud Agent - Python + Toolbox Plugin Demos
=================================================

This folder contains setups for multiple scenarios:

- A single agent networked with ngrok to be reachable from the outside world.
- An "Alice and Bob" demo for showing interactions between two agents.
- And a mediator networked with ngrok that can be mixed in with the single agent
  or Alice and Bob scenarios for demonstrating mediation.

Where applicable, agents are connected to the Sovrin BuilderNet to enable
credentials exchange. You can anchor your DID and become an endorser (able to
write schemas and credential definitions) at https://selfserve.sovrin.org.

## Disclaimer: On the usage of ngrok

For each of the scenarios listed above, ngrok is used to simplify networking
between the host and containers. As a result of the toolbox generally running
directly on the host and the containers needing to communicate with each other
as well as the host, there is not a platform agnostic method of using the same
endpoint from all perspectives and reaching the intended agent. On Linux, this
is as simple as using the `host` network mode. On Mac and Windows, since docker
itself essentially runs in a VM, networking is not so flexible. From within the
container, `localhost` points to itself, `docker.host.internal` points to the
host, and other containers are reached by service name. From the host,
containers are only reachable through ports on `localhost`. In theory, one could
add aliases to each container on the host machine but this adds setup steps that
are not easily reversed when the containers are stopped and removed.

To circumvent these complexities, ngrok is used in these demos to provide an
endpoint that is consistently reachable from both the container cohort and the
host. This also comes with the side benefit of the demo agents being accessible
to other agents if, for instance, you would like to experiment with agents with
a peer.

Ngrok is not without limitations. Requests will be throttled after exceeding a
certain threshold and endpoints will expire after a set length of time, usually
on the range of a few hours. This means all connections formed will also expire
after a few hours. **These setups are for demonstration purposes only and should
not be used in production.**

In practice, Aries Cloud Agent - Python is deployed behind typical web
infrastructure to provide a consistent endpoint.

## Running the Demos

Requirements:
- Docker
- Docker Compose

### Invitations

For each of the demo scenarios, "admin" invitations will be printed to the
console for each started agent. Paste these invitations into an instance of the
Aries Toolbox to form an "admin" connection and use the Toolbox to trigger
interactions with other agents.

#### Single Agent

Run the following from the `demo` directory:

```sh
$ docker-compose up --build
```

#### Alice + Bob

Run the following from the `demo` directory:

```sh
$ docker-compose -f ./docker-compose.alice-bob.yml up --build
```

#### Alice + Bob + Mediator

Run the following from the `demo` directory:

```sh
$ docker-compose \
    -f ./docker-compose.alice-bob.yml \
    -f ./docker-compose.mediator.yml \
	up --build
```

#### Single Agent + Mediator

Run the following from the `demo` directory:

```sh
$ docker-compose \
    -f ./docker-compose.yml \
    -f ./docker-compose.mediator.yml \
	up --build
```

#### Standalone Mediator

Run the following from the `demo` directory:

```sh
$ docker-compose \
    -f ./docker-compose.mediator.yml \
	up --build
```
