import asyncio
import sys
from pyrabbit.api import Client
from pyrabbit.http import HTTPError
import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
logger = logging.getLogger("monitoring:rabbitmq")


class RabbitmqMetric:
    def __init__(self, config):
        self.en = config['enable']
        self.connection_config = config['connection']
        self.update_interval = config['update-interval_sec']
        self.queues = config['queues']
        self.overview_metrics = config['overview-metrics']
        self.queue_metrics = config['queue-metrics']
        self.client = None
        if self.en:
            self.client = Client('{}:{}'.format(self.connection_config["host"],
                                                self.connection_config["port"]),
                                 self.connection_config["username"],
                                 self.connection_config["password"])

    async def measure_overview(self):
        try:
            info = {}
            if self.en and self.client is not None:
                overview = self.client.get_overview()
                if self.overview_metrics is not None and overview is not None:
                    for each in overview.keys():
                        if each in self.overview_metrics:
                            info.update({each:overview[each]})
                else:
                    if overview is not None and type(overview) is dict:
                        info.update(overview)
            await asyncio.sleep(self.update_interval)
            return info
        except Exception as e:
            logging.critical(e)
            sys.exit(-1)

    async def measure_queues(self):
        try:
            res = []
            if self.en and self.client is not None:
                try:
                    queues_information = self.client.get_queues('/')
                except HTTPError as err:
                    return res

                if self.queue_metrics is not None and self.queues is not None and queues_information is not None:
                    for queue_name in self.queues:
                        for queue_information in queues_information:
                            if queue_information['name'] == queue_name:
                                info = {}
                                for each in queue_information.keys():
                                    if each in self.queue_metrics:
                                        info.update({each: queue_information[each]})
                                res.append(info)
                                break
                else:
                    res = queues_information
            await asyncio.sleep(self.update_interval)
            return res
        except Exception as e:
            logging.critical(e)
            sys.exit(-1)