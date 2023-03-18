import asyncio
import logging

import aiohttp
from master.remote_workers_manager import RemoteWorkerManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkersPoller:
    def __init__(self, worker_manager: RemoteWorkerManager):
        self.worker_manager = worker_manager

    async def poll_workers(self) -> None:
        try:
            async with aiohttp.ClientSession() as self.session:
                await self._poll_workers()
        except Exception as e:
            logger.exception(f"Error in poll_workers, retrying after 60 sec: {e!r}")
            await asyncio.sleep(15)

    async def _poll_workers(self):
        self.worker_manager.session = self.session
        await self.worker_manager.initialize_workers_data()
        while True:
            tasks = [
                self.worker_manager.update_worker_data(worker)
                for worker in self.worker_manager.workers_data.values()
            ]
            await asyncio.gather(*tasks)
            await self.worker_manager.check_and_scale_workers()
            await asyncio.sleep(7)
