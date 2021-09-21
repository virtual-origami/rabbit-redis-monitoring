import asyncio
import sys
import redis
import logging

# logger for this file
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/tmp/tracker.log')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class RedisMetric:
    def __init__(self, config):
        self.en = config["enable"]
        self.host = config['connection']['host']
        self.port = config['connection']['port']
        self.username = config['connection']['username']
        self.password = config['connection']['password']
        self.update_interval = config['update-interval_sec']
        self.redis_metrics = config['metrics']
        self.db = None
        if self.en:
            self.db = redis.Redis(host=self.host, port=self.port, password=self.password)
            if self.db is not None:
                self.test_connection()

    def test_connection(self):
        try:
            self.db.ping()
        except Exception as e:
            logging.critical("Redis connection Error")
            logging.critical(e)
            sys.exit(-1)

    async def measure(self):
        info = {}
        if self.en and self.db is not None:
            overview = self.db.info()
            if self.redis_metrics is not None:
                for each in overview.keys():
                    if each in self.redis_metrics:
                        info.update({each: overview[each]})
            else:
                if overview is not None and type(overview) is dict:
                    info.update(overview)
        await asyncio.sleep(self.update_interval)
        return info
