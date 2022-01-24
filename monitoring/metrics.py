import sys
import queue
import json
import traceback

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
            traceback.format_exc()
            sys.exit(-1)

    @staticmethod
    def send_to_monitoring_service(metric):
        logger.debug(f'CALL: =============== send_to_monitoring_service V.1 ==========================')
        logger.debug(f'Metric: Keys: {metric["metrics"].keys()}')

        if 'network' in metric['metrics'].keys():
            if "latency" in metric['metrics']['network'].keys():
                logger.debug(f'RAINBOW: Network: Latency: {metric["metrics"]["network"]["latency"]}')
                latency_dict = metric["metrics"]["network"]["latency"]
                if latency_dict is not None:
                    if "average_latency" in latency_dict.keys():
                        logger.debug(f'RAINBOW: Network :average_latency: {latency_dict["average_latency"]}')

                        RainbowUtils.store(float(latency_dict["average_latency"]),
                                           'network_average_latency',
                                           latency_dict["units"]["latency"],
                                           'network_average_latency',
                                           minVal=0,
                                           higherIsBetter=False)

                    if "jitter" in latency_dict.keys():
                        logger.debug(f'RAINBOW: Network :jitter: {latency_dict["jitter"]}')
                        RainbowUtils.store(float(latency_dict["jitter"]),
                                           'network_jitter',
                                           latency_dict["units"]["jitter"],
                                           'network jitter',
                                           minVal=0,
                                           higherIsBetter=False)

        if "redis" in metric['metrics'].keys():
            redis_dict = metric['metrics']['redis']
            if redis_dict is not None:
                if "total_system_memory" in redis_dict.keys():
                    logger.debug(f'RAINBOW: Redis: total_system_memory:{redis_dict["total_system_memory"]}')
                    RainbowUtils.store(float(redis_dict["total_system_memory"]),
                                       'redis_total_system_memory',
                                       'bytes',
                                       'redis_total system memory',
                                       minVal=0,
                                       higherIsBetter=False)
                if "used_memory" in redis_dict.keys():
                    logger.debug(f'RAINBOW: Redis: used_memory:{redis_dict["used_memory"]}')
                    RainbowUtils.store(float(redis_dict["used_memory"]),
                                       'redis_used_memory',
                                       'bytes',
                                       'redis_used_memory',
                                       minVal=0,
                                       higherIsBetter=False)

        if "rabbitmq-queues" in metric['metrics'].keys():
            rabbitmq_queues = metric['metrics']["rabbitmq-queues"]
            if rabbitmq_queues is not None:
                for rabbit_q in rabbitmq_queues:
                    if 'name' in rabbit_q.keys():
                        pub_metric_name = rabbit_q["name"] + "_pub_rate"
                        deliver_metric_name = rabbit_q["name"] + "_deliver_rate"
                        if 'message_stats' in rabbit_q.keys():
                            # logger.debug(f'RAINBOW: Rabbitmq: name: {rabbit_q["name"]} : rate:{rabbit_q["message_stats"]}')
                            if 'publish_details' in rabbit_q["message_stats"].keys():
                                if 'rate' in rabbit_q["message_stats"]['publish_details'].keys():
                                    msg_rate = rabbit_q["message_stats"]['publish_details']["rate"]
                                    logger.debug(f"{pub_metric_name}: {msg_rate}")
                                    RainbowUtils.store(float(msg_rate),
                                                       pub_metric_name,
                                                       'messages/second',
                                                       'Rabbit mq publish_rate',
                                                       minVal=0,
                                                       higherIsBetter=False)
                            if 'deliver_details' in rabbit_q["message_stats"].keys():
                                if 'rate' in rabbit_q["message_stats"]['deliver_details'].keys():
                                    msg_rate = rabbit_q["message_stats"]['deliver_details']["rate"]
                                    logger.debug(f"{deliver_metric_name}: {msg_rate}")
                                    RainbowUtils.store(float(msg_rate),
                                                       deliver_metric_name,
                                                       'messages/second',
                                                       'Rabbit mq deliver_rate',
                                                       minVal=0,
                                                       higherIsBetter=False)