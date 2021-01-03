import asyncio
import yaml
import aiopg

import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

import reprlib
import logging
import signal
import pydevd_pycharm

import bot

reprlib.aRepr.maxother = 200
logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
elastic_log = logging.getLogger("elasticsearch")
elastic_log.setLevel(logging.ERROR)


async def sleeper():
    while True:
        await asyncio.sleep(3600)


async def init(config):
    async with aiopg.create_pool(config["postgres_uri"]) as pool:
        await bot.initialise(config, pool)
        await sleeper()


def handle_sigint(signum, frame):
    pydevd_pycharm.settrace(
        "192.168.11.34",
        port=12345,
        stdoutToServer=True,
        stderrToServer=True
    )
    exit()


def main():

    if config.get("sentry"):
        sentry_sdk.init(
            dsn=config["sentry"]["dns"],
            integrations=[AioHttpIntegration()]
        )

    signal.signal(signal.SIGINT, handle_sigint)
    loop = asyncio.get_event_loop()

    loop.run_until_complete(init(config))


if __name__ == '__main__':
    with open("config.yaml") as conf_file:
        config = yaml.load(conf_file, Loader=yaml.SafeLoader)
    main()
