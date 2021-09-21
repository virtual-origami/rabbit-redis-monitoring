import asyncio
import time
import numpy as np
from tcp_latency import measure_latency
from bittivahti.bittivahti import Bittivahti


class NetworkMetrics:
    def __init__(self, config):

        self.latency_config = config["latency"]
        self.latency_en = self.latency_config["enable"]
        self.interfaces = self.latency_config["interfaces"]
        self.latency_metrics = self.latency_config['metrics']
        self.jitter = 0
        self.connection_status = False
        self.latency_points = np.zeros(self.latency_config["max-latency-metric-count"]).tolist()
        self.avg_latency = 0

        self.bandwidth_config = config["bandwidth"]
        self.bw_en = self.bandwidth_config["enable"]
        self.bw_metrics = self.bandwidth_config['metrics']
        self.bandwidth = Bittivahti()

    async def measure_network_latency_n_jitter(self):
        info = {}
        units = {}
        if self.latency_en:
            latency_measurements = measure_latency(host=self.latency_config["connection"]["host"],
                                                   port=self.latency_config["connection"]["port"],
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

            if self.latency_metrics is None:
                info.update({"average_latency": self.avg_latency})
                units.update({"latency": self.latency_config["units"]["latency"]})
                info.update({"jitter": self.jitter})
                units.update({"jitter": self.latency_config["units"]["jitter"]})
            else:
                if 'latency' in self.latency_metrics:
                    info.update({"average_latency": self.avg_latency})
                    units.update({"latency": self.latency_config["units"]["latency"]})

                if 'jitter' in self.latency_metrics:
                    info.update({"jitter": self.jitter})
                    units.update({"jitter": self.latency_config["units"]["jitter"]})

            info.update({"units": units})

        await asyncio.sleep(self.latency_config["update-interval_sec"])
        return info

    async def measure_bandwidth(self):
        device_list = []
        if self.bw_en:
            self.bandwidth.update_state()
            for iface in sorted(self.bandwidth.device.keys()):
                if iface in self.interfaces:
                    rx, tx, rxp, txp = [x / self.bandwidth.period for x in self.bandwidth.delta[iface]]

                    info = {}
                    units = {}

                    if self.bw_metrics is None:
                        units.update({'receive-bandwidth': self.bandwidth_config["units"]["receive-bandwidth"]})
                        info.update({'receive-bandwidth': rx * 8})
                        units.update({'transmit-bandwidth': self.bandwidth_config["units"]["transmit-bandwidth"]})
                        info.update({'transmit-bandwidth': tx * 8})
                        units.update({'receive-packet': self.bandwidth_config["units"]["receive-packet"]})
                        info.update({'receive-packet': rxp})
                        units.update({'transmit-packet': self.bandwidth_config["units"]["transmit-packet"]})
                        info.update({'transmit-packet': txp})
                        info.update({'interface': iface})
                    else:
                        if 'receive-bandwidth' in self.bw_metrics:
                            units.update({'receive-bandwidth': self.bandwidth_config["units"]["receive-bandwidth"]})
                            info.update({'receive-bandwidth': rx * 8})

                        if 'transmit-bandwidth' in self.bw_metrics:
                            units.update({'transmit-bandwidth': self.bandwidth_config["units"]["transmit-bandwidth"]})
                            info.update({'transmit-bandwidth': tx * 8})

                        if 'receive-packet' in self.bw_metrics:
                            units.update({'receive-packet': self.bandwidth_config["units"]["receive-packet"]})
                            info.update({'receive-packet': rxp})

                        if 'transmit-packet' in self.bw_metrics:
                            units.update({'transmit-packet': self.bandwidth_config["units"]["transmit-packet"]})
                            info.update({'transmit-packet': txp})

                        if 'interface' in self.bw_metrics:
                            info.update({'interface': iface})

                    info.update({'units': units})
                    device_list.append(info)

        await asyncio.sleep(self.bandwidth_config["update-interval_sec"])
        return device_list

    async def measure(self):
        info = {}
        if self.latency_en:
            latency_res = await self.measure_network_latency_n_jitter()
            info.update({'latency': latency_res})
        if self.bw_en:
            bw_res = await self.measure_bandwidth()
            info.update({'bandwidth': bw_res})
        return info
