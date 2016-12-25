# Climulon

[![Build Status](https://travis-ci.org/Shrobs/climulon.svg?branch=master)](https://travis-ci.org/Shrobs/climulon)

Climulon is a CLI that eases the process of managing complex infrastructure and deployments of docker containers in AWS, while being faithful to the tenets of infrastructure-as-code.

It goes this way :
- Describe your infrastructure and add it to your repo
- Provision with Climulon
- Deploy with Climulon

## Description

Climulon is a CLI that takes care of provisionning and decommissioning a set of cloudformation templates in AWS, in a modular fashion. Each template of the set can be duplicated, modified or changed, or removed on its own, without impacting the set.
It also takes care of deploying docker images to AWS ECS, and checking the status of the scheduler that is running them.

Climulon consumes configuration files using a templating language similar to the AWS Cloudformation one, to link the multiple templates that describe the infrastructure and the scheduler that runs the docker containers.

## Getting started 

### Prerequisites

Climulon runs on python 3 only.
Its only dependency is `boto3`

### Installing

You can either install Climulon's dependencies, or either build its docker image.

To install Climulon's dependencies, run the following :
- If your system have python 3 as default version:
```
pip install -r requirements.txt
```
- If your system have python 2 as default version, make sure that python 3 and pip 3 are installed, and run the following :
```
pip3 install -r requirements.txt
```

If you want to run Climulon by building its docker image, just build it locally :
```
docker build
```

You can also download the docker image directy from docker hub :
```
docker pull shrobs/climulon:latest
```

### Using the CLI

#### Live examples

You can test how **Climulon** works by trying these two projects :
- [Django app](https://github.com/Shrobs/climulon-example-python)
- [Node express app](https://github.com/Shrobs/climulon-example-nodejs)

Just follow the instructions on the readmes.

#### Provisionning 

An environment can be provisionned using a single command :
```
climulon provision -c infrastructure.json
```
Where `infrastructure.json` is a config file describing your whole infrastructure.
Detailed examples can be found in the Live examples section

#### Decommission

An environment can be decommission using a single command :
```
climulon decommission -c infrastructure.json
```
Where `infrastructure.json` is a config file describing your whole infrastructure.
Detailed examples can be found in the Live examples section

#### Deployment

Documentation in progress

#### Status check

An environment can be decommission using a single command :
```
climulon status -c infrastructure.json
```
Where `infrastructure.json` is a config file describing your whole infrastructure.
Detailed examples can be found in the Live examples section

