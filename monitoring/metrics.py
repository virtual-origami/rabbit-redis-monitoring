import sys
import queue
import json
from monitoring.network import NetworkMetrics
from monitoring.rabbitmq import RabbitmqMetric
from monitoring.redis import RedisMetric

import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
logger = logging.getLogger("monitoring:metrics")


class Metrics:
    def __init__(self, config):
        self.network_metric = NetworkMetrics(config=config["network"])
        self.rabbitmq_metric = RabbitmqMetric(config=config["rabbitmq"])
        self.redis_metric = RedisMetric(config=config["redis"])

    async def start(self):
        await self.network_metric.start()
        await self.rabbitmq_metric.start()
        await self.redis_metric.start()

    async def measure(self):
        """
        measure metric in 3 categories
        1. network
        2. rabbitmq
        3. redis
        Good point to start integrating with other monitoring tools
        :return:
        """
        try:
            nw_metric = await self.network_metric.measure()
            rabbit_ovr_metric = await self.rabbitmq_metric.measure_overview()
            rabbit_q_metric = await self.rabbitmq_metric.measure_queues()
            redis_metric = await self.redis_metric.measure()

            measurements = \
                {
                    'metrics': {
                        'network': nw_metric,
                        'rabbitmq-overview': rabbit_ovr_metric,
                        'rabbitmq-queues': rabbit_q_metric,
                        'redis': redis_metric,
                    }
                }

            return json.dumps(measurements)
        except Exception as e:
            logging.critical(e)
            sys.exit(-1)
