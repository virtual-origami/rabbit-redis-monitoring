import asyncio
import queue
import sys
import redis
import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
logger = logging.getLogger("monitoring:redis")


class RedisMetric:
    def __init__(self, config):
        self.en = config["enable"]
        self.host = config['connection']['host']
        self.port = config['connection']['port']
        self.username = config['connection']['username']
        self.password = config['connection']['password']
        self.update_interval = config['update-interval_sec']
        self.redis_metrics = config['metrics']
        self.measurement_queue = queue.SimpleQueue()
        self.db = None
        if self.en:
            try:
                self.db = redis.Redis(host=self.host, port=self.port, password=self.password)
            except redis.ConnectionError as e:
                logging.critical(e)
                sys.exit(-1)

    def test_connection(self):
        try:
            self.db.ping()
        except Exception as e:
            logging.critical(e)
            sys.exit(-1)

    async def start(self):
        asyncio.create_task(self.run())

    async def run(self):
        try:
            while True:
                if self.en and self.db is not None:
                    info = {}
                    overview = self.db.info()
                    if self.redis_metrics is not None:
                        for each in overview.keys():
                            if each in self.redis_metrics:
                                info.update({each: overview[each]})
                    else:
                        if overview is not None and type(overview) is dict:
                            info.update(overview)
                    self.measurement_queue.put_nowait(item=info)
                await asyncio.sleep(self.update_interval)
        except Exception as e:
            logging.critical(e)
            sys.exit(-1)

    async def measure(self):
        try:
            measurement = self.measurement_queue.get_nowait()
            return measurement
        except queue.Empty as e:
            return None
