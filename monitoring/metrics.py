from monitoring.network import NetworkMetrics
from monitoring.rabbitmq import RabbitmqMetric
from monitoring.redis import RedisMetric


class Metrics:
    def __init__(self, config):
        self.network_metric = NetworkMetrics(config=config["network"])
        self.rabbitmq_metric = RabbitmqMetric(config=config["rabbitmq"])
        self.redis_metric = RedisMetric(config=config["redis"])

    async def update(self):
        print(f'Network: {await self.network_metric.measure()}')
        print(f'RabbitMQ: {await self.rabbitmq_metric.measure_overview()}')
        for m in await self.rabbitmq_metric.measure_queues():
            print(f'RabbitMQ: {m}')
        print(f'Redis: {await self.redis_metric.measure()}')
