# monitoring

This repository python module for monitoring following

- Redis server
- RabbitMQ broker
- Network 
  - Latency
  - Jitter
  - Bandwidth



## Development

### Python3.x

1. Create a Virtual Environment

   ```bash
   $ virtualenv -m venv venv
   ```

2. Activate Virtual Environment

   ```bash
   $ . venv/bin/activate 
   ```

3. Install the Dependencies

   ```bash
   $ pip install -r requirements.txt
   ```

4. Install `monitoring` as python package for development:

   ```bash
   $ pip install -e .
   ```

   This makes the `monitoring` binary available as a CLI

### Usage

Run `monitoring` binary using command line:

- -c configuration file path/name

```bash
$ monitoring -c config.yaml
```



## Dependencies

### Message Broker (RabbitMQ)

Use the [rabbitmqtt](https://github.com/virtual-origami/rabbitmqtt) stack for the Message Broker

__NOTE__: The `rabbitmqtt` stack needs an external docker network called `iotstack` make sure to create one using `docker network create iotstack`



### In-memory database (Redis)

Use the [redis](https://github.com/virtual-origami/rabbitmqtt) stack for the Redis server

__NOTE__: The `redis` stack needs an external docker network called `iotstack` make sure to create one using `docker network create iotstack`



## Docker

1. To build Docker Images locally use:

   ```bash
   $ docker build -t monitoring:<version> .
   ```

2. To run the Application along with the RabbitMQ Broker and Redis Server connect the container with the `iotstack` network using:

   ```bash
   $ docker run --rm --network=iotstack -t monitoring:<version> -c config.yaml
   ```

   __INFO__: Change the broker address in the `config.yaml` file to `rabbitmq` (name of the RabbitMQ Container in _rabbitmqtt_ stack) and change redis server address in the `config.yaml` file to `redis` (name of the Redis Container in _redis_ stack) 

3. To run the a custom configuration for the Container use:

   ```bash
   $ docker run --rm -v $(pwd)/config.yaml:/monitoring/config.yaml --network=iotstack -t monitoring:<version> -c config.yaml
   ```

## Maintainers
The repository is maintained by:

- [Karthik Shenoy Panambur](mailto:she@biba.uni-bremen.de)
- [Shantanoo Desai](mailto:des@biba.uni-bremen.de)

[__BIBA - Bremer Institut für Produktion und Logistik GmbH__](www.biba.uni-bremen.de)

## FUNDING

* The development of this codebase and repository is driven through the [RAINBOW Project](https://rainbow-h2020.eu/). RAINBOW Project has received funding from the European Union’s Horizon 2020 programme under grant agreement number __871403__
* The development of this codebase and repository is driven through the [ASSURED Project](https://www.project-assured.eu/). ASSURED project is funded by the European Union's Horizon 2020 programme under Grant Agreement number __952697__
