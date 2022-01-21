import asyncio
import queue
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
        self.overview_measurement_queue = queue.SimpleQueue()
        self.queue_stat_measurement_queue = queue.SimpleQueue()
        self.client = None
        if self.en:
            self.client = Client('{}:{}'.format(self.connection_config["host"],
                                                self.connection_config["port"]),
                                 self.connection_config["username"],
                                 self.connection_config["password"])

    async def start(self):
        asyncio.create_task(self.run())

    async def run(self):
        try:
            while True:
                if self.en and self.client is not None:

                    info = {}
                    res = []

                    overview = self.client.get_overview()
                    if self.overview_metrics is not None and overview is not None:
                        for each in overview.keys():
                            if each in self.overview_metrics:
                                info.update({each: overview[each]})
                    else:
                        if overview is not None and type(overview) is dict:
                            info.update(overview)
                    self.overview_measurement_queue.put_nowait(item=info)

                    queues_information = self.client.get_queues('/')
                    if self.queue_metrics is not None and self.queues is not None and queues_information is not None:
                        for queue_name in self.queues:
                            for queue_information in queues_information:
                                if queue_information['name'] == queue_name:
                                    info = {}
                                    if 'name' in queue_information.keys():
                                        info.update({'name': queue_information['name']})
                                    if 'message_stats' in queue_information.keys():
                                        info.update({'message_stats': queue_information['message_stats']})
                                    res.append(info)
                                    break
                    else:
                        res = queues_information
                    self.queue_stat_measurement_queue.put_nowait(item=res)
                await asyncio.sleep(self.update_interval)
        except HTTPError as err:
            return []
        except Exception as e:
            logging.critical(e)
            sys.exit(-1)

    async def measure_overview(self):
        try:
            measurement = self.overview_measurement_queue.get_nowait()
            return measurement
        except queue.Empty as e:
            return None

    async def measure_queues(self):
        try:
            measurement = self.queue_stat_measurement_queue.get_nowait()
            return measurement
        except queue.Empty as e:
            return None
