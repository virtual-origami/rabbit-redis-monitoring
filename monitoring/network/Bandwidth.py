import asyncio
import queue
from bittivahti.bittivahti import Bittivahti
import sys
import logging

logger = logging.getLogger("monitoring:bandwidth")
logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format='%(levelname)-2s [%(filename)s:%(lineno)d] %(message)s')


class Bandwidth:
    def __init__(self, config):
        self.enable = config["enable"]
        self.measurable_metrics = config['metrics']
        self.update_interval_sec = config['update-interval_sec']
        self.units = config['units']
        self.interfaces = config["interfaces"]
        self.bandwidth = Bittivahti()
        self.measurement_queue = queue.SimpleQueue()

    async def run(self):
        try:
            while True:
                if self.enable:
                    device_list = []
                    self.bandwidth.update_state()
                    for iface in sorted(self.bandwidth.device.keys()):
                        if iface in self.interfaces:
                            rx, tx, rxp, txp = [x / self.bandwidth.period for x in self.bandwidth.delta[iface]]

                            info = {}
                            units = {}

                            if self.measurable_metrics is None:
                                units.update({'receive-bandwidth': self.units["receive-bandwidth"]})
                                info.update({'receive-bandwidth': rx * 8})
                                units.update({'transmit-bandwidth': self.units["transmit-bandwidth"]})
                                info.update({'transmit-bandwidth': tx * 8})
                                units.update({'receive-packet': self.units["receive-packet"]})
                                info.update({'receive-packet': rxp})
                                units.update({'transmit-packet': self.units["transmit-packet"]})
                                info.update({'transmit-packet': txp})
                                info.update({'interface': iface})
                            else:
                                if 'receive-bandwidth' in self.measurable_metrics:
                                    units.update({'receive-bandwidth': self.units["receive-bandwidth"]})
                                    info.update({'receive-bandwidth': rx * 8})

                                if 'transmit-bandwidth' in self.measurable_metrics:
                                    units.update(
                                        {'transmit-bandwidth': self.units["transmit-bandwidth"]})
                                    info.update({'transmit-bandwidth': tx * 8})

                                if 'receive-packet' in self.measurable_metrics:
                                    units.update({'receive-packet': self.units["receive-packet"]})
                                    info.update({'receive-packet': rxp})

                                if 'transmit-packet' in self.measurable_metrics:
                                    units.update({'transmit-packet': self.units["transmit-packet"]})
                                    info.update({'transmit-packet': txp})

                                if 'interface' in self.measurable_metrics:
                                    info.update({'interface': iface})

                            info.update({'units': units})
                            device_list.append(info)
                    if device_list is not None:
                        self.measurement_queue.put_nowait(item=device_list)
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
