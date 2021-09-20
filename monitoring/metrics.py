from monitoring.network import NetworkMetrics


class Metrics:
    def __init__(self, config):
        self.network_metric = NetworkMetrics(config=config["network"])

    async def update(self):
        print(f'Latency and jitter: {await self.network_metric.measure_network_latency_n_jitter()}')
        print(f'Bandwidth: {await self.network_metric.measure_bandwidth()}')
