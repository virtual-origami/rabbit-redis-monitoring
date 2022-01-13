import argparse
import asyncio
import functools
import os
import re
import signal
import sys
import yaml
import logging
from monitoring.metrics import Metrics
from monitoring.health import HealthServer

logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')

# logger for this file
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/tmp/robogen.log')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

is_sighup_received = False
metric_monitor = None

# YAML configuration to read Environment Variables in Configuration File
env_pattern = re.compile(r".*?\${(.*?)}.*?")


def env_constructor(loader, node):
    value = loader.construct_scalar(node)
    for group in env_pattern.findall(value):
        value = value.replace(f"${{{group}}}", os.environ.get(group))
    return value


yaml.add_implicit_resolver("!pathex", env_pattern)
yaml.add_constructor("!pathex", env_constructor)


def _graceful_shutdown():
    global metric_monitor
    if metric_monitor is not None:
        del metric_monitor


def parse_arguments():
    """Arguments to run the script"""
    parser = argparse.ArgumentParser(description='Robotic Arm Motion Generator')
    parser.add_argument('--config', '-c', required=True, help='YAML Configuration File for RobotMotionGen with path')
    return parser.parse_args()


def sighup_handler(name):
    """SIGHUP HANDLER"""
    # logger.debug(f'signal_handler {name}')
    logger.info('Updating the Metric Configuration')
    global is_sighup_received
    is_sighup_received = True


def read_config(yaml_config_file, root_key):
    """Parse the given Configuration File"""
    if os.path.exists(yaml_config_file):
        with open(yaml_config_file, 'r') as config_file:
            yaml_as_dict = yaml.load(config_file, Loader=yaml.FullLoader)
        return yaml_as_dict[root_key]
    else:
        logger.error('YAML Configuration File not Found.')
        raise FileNotFoundError


async def app(eventloop, config):
    """Main application for Robot Generator"""
    global metric_monitor
    global is_sighup_received

    while True:
        # Read configuration
        try:
            metric_monitor_config = read_config(config, "monitoring")
        except Exception as e:
            logger.error('Error while reading configuration:')
            logger.error(e)
            break

        # health server
        health_server = HealthServer(config=metric_monitor_config["health_server"], event_loop=eventloop)
        eventloop.create_task(health_server.server_loop())

        metric_monitor_read_rate = metric_monitor_config["measurement-read-interval_sec"]
        metric_monitor = Metrics(config=metric_monitor_config)

        # start the metric monitoring
        await metric_monitor.start()

        # continuously monitor signal handle and update robot motion
        while not is_sighup_received:
            print(f'{await metric_monitor.measure()}')
            await asyncio.sleep(metric_monitor_read_rate)

        # If SIGHUP Occurs, Delete the instances
        _graceful_shutdown()

        # reset sighup handler flag
        is_sighup_received = False


def app_main():
    """Initialization"""
    args = parse_arguments()
    if not os.path.isfile(args.config):
        logging.error("configuration file not readable. Check path to configuration file")
        sys.exit(-1)

    event_loop = asyncio.get_event_loop()
    event_loop.add_signal_handler(signal.SIGHUP, functools.partial(sighup_handler, name='SIGHUP'))
    try:
        event_loop.run_until_complete(app(event_loop, args.config))
    except KeyboardInterrupt:
        logger.error('CTRL+C Pressed')
        _graceful_shutdown()

