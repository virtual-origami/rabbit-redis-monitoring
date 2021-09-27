import asyncio
import queue
from tcp_latency import measure_latency
import sys
import logging

logger = logging.getLogger("monitoring:latency")
logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format='%(levelname)-2s [%(filename)s:%(lineno)d] %(message)s')


class LatencyJitter:
    def __init__(self, config):
        self.enable = config["enable"]
        self.measurable_metrics = config['metrics']
        self.connection = config['connection']
        self.network_time_out = config['network-timeout_sec']
        self.min_metric_count_for_averaging = config["min-metric-count-for-averaging"]
        self.update_interval_sec = config['update-interval_sec']
        self.units = config['units']
        self.latency_data_collection = []
        self.avg_latency = 0
        self.avg_jitter = 0
        self.measurement_queue = queue.SimpleQueue()

    def calculate_avg_latency(self):
        if len(self.latency_data_collection) > 0:
            sum_latency = 0
            for latency_point in self.latency_data_collection:
                sum_latency += latency_point
            return sum_latency / len(self.latency_data_collection)
        return None

    def calculate_avg_jitter(self):
        """
        # jitter calculation taken from https://www.pingman.com/kb/article/what-is-jitter-57.html
        :return:
        """
        if len(self.latency_data_collection) > 1:
            sum_jitter = 0
            for i in range(0, len(self.latency_data_collection) - 1):
                sum_jitter += abs(self.latency_data_collection[i] - self.latency_data_collection[i + 1])
            return sum_jitter / (len(self.latency_data_collection) - 1)
        return None

    async def run(self):
        try:
            while True:
                if self.enable:
                    latency_measurements = measure_latency(host=self.connection["host"],
                                                           port=self.connection["port"],
                                                           timeout=self.network_time_out,
                                                           runs=1,
                                                           wait=0)
                    latency_point = latency_measurements[0]
                    if latency_point is not None:
                        info = {}
                        units = {}
                        self.latency_data_collection.append(latency_point)
                        if len(self.latency_data_collection) > self.min_metric_count_for_averaging:
                            self.latency_data_collection.pop(0)
                            self.avg_jitter = self.calculate_avg_jitter()
                            self.avg_latency = self.calculate_avg_latency()
                            if self.measurable_metrics is None:
                                info.update({"average_latency": self.avg_latency})
                                units.update({"latency": self.units["latency"]})
                                info.update({"jitter": self.avg_jitter})
                                units.update({"jitter": self.units["jitter"]})
                            else:
                                if 'latency' in self.measurable_metrics:
                                    info.update({"average_latency": self.avg_latency})
                                    units.update({"latency": self.units["latency"]})

                                if 'jitter' in self.measurable_metrics:
                                    info.update({"jitter": self.avg_jitter})
                                    units.update({"jitter": self.units["jitter"]})

                            info.update({"units": units})
                            self.measurement_queue.put_nowait(item=info)
                await asyncio.sleep(self.update_interval_sec)
        except Exception as e:
            logging.critical(e)
            sys.exit(-1)

    async def measure(self):
        try:
            measurement = self.measurement_queue.get_nowait()
            return measurement
        except queue.Empty as e:
            return None
