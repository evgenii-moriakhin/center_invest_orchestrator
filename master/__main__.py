import asyncio
import json
import os

from aiohttp import web
from master.remote_workers_manager import RemoteWorkerManager
from master.workers_poller import WorkersPoller
from master.orchestrator_api import OrchestratorAPI


async def main():
    with open(os.getenv("CONFIG_MASTER")) as config_file:
        config = json.load(config_file)

    worker_manager = RemoteWorkerManager(
        app_info=config["app_info"],
        worker_info=config["worker_info"],
        worker_limits=config["worker_limits"],
        virtual_machines=config["virtual_machines"],
    )

    orchestrator_api = OrchestratorAPI(worker_manager)
    api_app = orchestrator_api.create_app()
    runner = web.AppRunner(api_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", os.getenv("MASTER_API_PORT"))
    await site.start()

    workers_poller = WorkersPoller(worker_manager)
    await workers_poller.poll_workers()


if __name__ == "__main__":
    asyncio.run(main())
