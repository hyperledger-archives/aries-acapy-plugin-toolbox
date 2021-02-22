Running ACA-Py with the Toolbox Plugin
======================================

To build the container:

```sh
$ docker build -t acapy-toolbox .
```

To start an agent using the default configuration:

```sh
$ docker run -it -p 3000:3000 -p 3001:3001 --rm acapy-toolbox start
```

For development purposes, it is often useful to use local versions of the code
rather than rebuilding a new container with the changes.

To start an agent using the default configuration and local versions of ACA-Py
and/or the toolbox plugin (paths must be adapted to your environment):

```sh
$ docker run -it -p 3000:3000 -p 3001:3001 --rm \
	-v ../aries-cloudagent-python/aries_cloudagent:/home/indy/site-packages/aries_cloudagent:z \
	-v ../aries-acapy-plugin-toolbox/acapy_plugin_toolbox:/home/indy/aries-acapy-plugin-toolbox/acapy_plugin_toolbox:z \
	acapy-toolbox
```
