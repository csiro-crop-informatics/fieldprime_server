
FieldPrime

This is the FieldPrime server REST-API for the FieldPrime scoring app. 

It is a python/flask web application with a mysql backend.

Building and Deploying:

The FieldPrime server can be deployed manually by copied the required files and setting up apache/mysql. It can also be built with docker/docker-compose simply by:

> docker-compose build
> docker-compose up


Configuration:

Default configutaion options (fpa/fp_common/default_config.py) can be over-ridden in fpa/fp_common/config.py

SSL certificates should be placed in sslCerts for surver to be able to use https
