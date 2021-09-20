import asyncio
import time
import numpy as np
from tcp_latency import measure_latency
from bittivahti.bittivahti import Bittivahti
from bittivahti.utils import pretty_unit as pu


class NetworkMetrics:
    def __init__(self, config):
        self.latency_config = config["latency"]
        self.bandwidth_config = config["bandwidth"]

        self.jitter = 0
        self.connection_status = False
        self.latency_points = np.zeros(self.latency_config["max-latency-metric-count"]).tolist()
        self.avg_latency = 0

        self.bandwidth = Bittivahti()

    async def measure_network_latency_n_jitter(self):
        while True:
            latency_measurements = measure_latency(host=self.latency_config["host"],
                                                   port=self.latency_config["port"],
                                                   timeout=self.latency_config["network-timeout_sec"],
                                                   runs=1,
                                                   wait=0)
            latency_point = latency_measurements[0]
            if latency_point is None:
                self.connection_status = False
            else:
                self.connection_status = True
                self.latency_points.append(latency_point)
                if len(self.latency_points) > self.latency_config["max-latency-metric-count"]:
                    self.latency_points.pop(0)
                    self.jitter = np.var(self.latency_points)
                    self.avg_latency = np.average(self.latency_points)
            await asyncio.sleep(self.latency_config["update-interval_sec"])
            return {
                "average_latency": self.avg_latency,
                "latency_unit": self.latency_config["latency-unit"],
                "jitter": self.jitter,
                "jitter_unit": self.latency_config["jitter-unit"],
            }

    async def measure_bandwidth(self):
        while True:
            self.bandwidth.update_state()
            device_list = []
            for iface in sorted(self.bandwidth.device.keys()):
                rx, tx, rxp, txp = [x / self.bandwidth.period for x in self.bandwidth.delta[iface]]
                rx_t, tx_t, rxp_t, txp_t = self.bandwidth.total[iface]
                d = {'iface': iface,
                     'rx-bw': rx,
                     'rx-bw-unit': self.bandwidth_config["receive-bandwidth-unit"],
                     'tx': tx,
                     'tx-bw-unit': self.bandwidth_config["transmit-bandwidth-unit"],
                     'rxp': rxp,
                     'rxp-unit': self.bandwidth_config["receive-packet-unit"],
                     'txp': txp,
                     'txp-unit': self.bandwidth_config["transmit-packet-unit"],
                     }
                if d["iface"] == "wlp6s0":
                    device_list.append(d)

            await asyncio.sleep(self.bandwidth_config["update-interval_sec"])
            return device_list
