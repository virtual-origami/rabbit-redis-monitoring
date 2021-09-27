import asyncio
import sys
import logging
from .LatencyJitter import LatencyJitter
from .Bandwidth import Bandwidth

logger = logging.getLogger("monitoring:network")
logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format='%(levelname)-2s [%(filename)s:%(lineno)d] %(message)s')


class NetworkMetrics:
    def __init__(self, config):
        self.latency_jitter = LatencyJitter(config=config['latency'])
        self.bandwidth = Bandwidth(config=config['bandwidth'])

    async def start(self):
        if self.latency_jitter.enable:
            asyncio.create_task(self.latency_jitter.run())
        if self.bandwidth.enable:
            asyncio.create_task(self.bandwidth.run())

    async def measure(self):
        try:
            info = {}
            latency_res = await self.latency_jitter.measure()
            info.update({'latency': latency_res})
            bw_res = await self.bandwidth.measure()
            info.update({'bandwidth': bw_res})
            return info
        except Exception as e:
            logging.critical(e)
            sys.exit(-1)
