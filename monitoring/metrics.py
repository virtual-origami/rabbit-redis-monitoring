import sys
import queue
import json
from monitoring.network import NetworkMetrics
from monitoring.rabbitmq import RabbitmqMetric
from monitoring.redis import RedisMetric
from RainbowMonitoringSDK.utils.annotations import RainbowUtils

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
            self.send_to_monitoring_service(metric=measurements)
            return json.dumps(measurements)
        except Exception as e:
            logging.critical(e)
            sys.exit(-1)

    @staticmethod
    def send_to_monitoring_service(metric):
        logger.debug(f'CALL: =============== send_to_monitoring_service ==========================')
        logger.debug(f'Metric: Keys: {metric.keys()}')
        if "latency" in metric.keys():
            logger.debug(f'RAINBOW: Network: Latency: {metric["latency"]}')
            if "average_latency" in metric['latency'].keys():
                logger.debug(f'RAINBOW: Network :average_latency: {metric["latency"]["average_latency"]}')
                RainbowUtils.store(float(metric["latency"]["average_latency"]),
                                   'network_average_latency',
                                   metric["latency"]["units"]["latency"],
                                   'network latency',
                                   minVal=0,
                                   higherIsBetter=False)
            if "jitter" in metric['latency'].keys():
                logger.debug(f'RAINBOW: Network :jitter: {metric["latency"]["jitter"]}')
                RainbowUtils.store(float(metric["latency"]["jitter"]),
                                   'network_jitter',
                                   metric["latency"]["units"]["jitter"],
                                   'network jitter',
                                   minVal=0,
                                   higherIsBetter=False)
        if "bandwidth" in metric.keys():
            if "receive-bandwidth" in metric['bandwidth'].keys():
                logger.debug(f'RAINBOW: Network: receive-bandwidth: {metric["bandwidth"]["receive-bandwidth"]}')
                RainbowUtils.store(float(metric["bandwidth"]["receive-bandwidth"]),
                                   'network_receive_bandwidth',
                                   metric["bandwidth"]["units"]["receive-bandwidth"],
                                   'receive bandwidth',
                                   minVal=0,
                                   higherIsBetter=False)
            if "transmit-bandwidth" in metric['bandwidth'].keys():
                logger.debug(f'RAINBOW: Network: transmit-bandwidth: {metric["bandwidth"]["transmit-bandwidth"]}')
                RainbowUtils.store(float(metric["bandwidth"]["transmit-bandwidth"]),
                                   'network_transmit_bandwidth',
                                   metric["bandwidth"]["units"]["transmit-bandwidth"],
                                   'receive bandwidth',
                                   minVal=0,
                                   higherIsBetter=False)
        if "redis" in metric.keys():
            if "total_system_memory" in metric['redis'].keys():
                logger.debug(f'RAINBOW: Redis: total_system_memory:{metric["redis"]["total_system_memory"]}')
                RainbowUtils.store(float(metric["redis"]["total_system_memory"]),
                                   'total_system_memory',
                                   'bytes',
                                   'total system memory',
                                   minVal=0,
                                   higherIsBetter=False)
            if "used_memory" in metric['redis'].keys():
                logger.debug(f'RAINBOW: Redis: used_memory:{metric["redis"]["used_memory"]}')
                RainbowUtils.store(float(metric["redis"]["used_memory"]),
                                   'used_memory',
                                   'bytes',
                                   'used memory',
                                   minVal=0,
                                   higherIsBetter=False)

        if "rabbitmq_queues" in metric.keys():
            for rabbit_q in metric["rabbitmq_queues"]:
                logger.debug(f'RAINBOW: Rabbitmq: name: {rabbit_q["messages_ready_details"]["name"]} : '
                             f'rate:{float(rabbit_q["messages_ready_details"]["rate"])}')
                RainbowUtils.store(float(rabbit_q["messages_ready_details"]["rate"]),
                                   rabbit_q["messages_ready_details"]["name"],
                                   'messages/second',
                                   'message rate',
                                   minVal=0,
                                   higherIsBetter=False)