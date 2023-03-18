import asyncio
import os
import uuid
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RemoteWorkerManager:
    def __init__(self, app_info: dict, worker_info: dict, worker_limits: Dict[str, int], virtual_machines: List[str]):
        self.worker_limits = worker_limits
        self.virtual_machines = virtual_machines
        self.workers_data = {}
        self.worker_port = str(worker_info["port"])
        self.app_port = str(app_info.get("app_port", ""))
        self.worker_git_repo = worker_info.get("git_repo", "")
        self.worker_dockerfile = worker_info.get("dockerfile", "")
        self.healthcheck_api = app_info.get("healthcheck", "")
        self.app_image = app_info.get("image", "")
        self.app_git_repo = app_info.get("git_repo", "")
        self.app_dockerfile = app_info.get("dockerfile", "")
        self.worker_operation_lock = asyncio.Lock()
        self.worker_data_lock = asyncio.Lock()
        self.session = None
        self.ssh_user = os.getenv("SSH_USER")
        if not self.ssh_user:
            raise RuntimeError("no SSH_USER env variable provided for ssh remote VMs")

        logger.info("WorkerManager initialized with app_info and worker_info.")

    async def set_worker_value_data(self, worker_name, key, value):
        async with self.worker_data_lock:
            self.workers_data[worker_name][key] = value

    async def set_worker_data(self, worker_name, data):
        async with self.worker_data_lock:
            if worker_name in self.workers_data:
                self.workers_data[worker_name].update(**data)
            else:
                self.workers_data[worker_name] = data

    async def del_worker_data(self, worker_name):
        async with self.worker_data_lock:
            del self.workers_data[worker_name]

    async def check_and_scale_workers(self) -> None:
        healthy_workers = 0
        min_workers = self.worker_limits["min_workers"]
        max_workers = self.worker_limits["max_workers"]

        for worker_name, worker_data in dict(**self.workers_data).items():
            if not self.is_app_healthy(worker_name):
                if self.is_app_failed_worker_running(worker_name) and "host" in worker_data:
                    await self.start_app(worker_name, worker_data["host"])
                else:
                    logger.warning(f"Worker {worker_name} is not healthy, restarting...")
                    await self.restart_worker(worker_name)
                    continue

            healthy_workers += 1
            memory_usage = worker_data.get("memory_usage", 0)
            cpu_usage = worker_data.get("cpu_usage", 0)

            if memory_usage >= self.worker_limits["memory_limit"] or \
                    cpu_usage >= self.worker_limits["cpu_limit"]:
                logger.info(f"Worker {worker_name} reached resource limits, trying to deploy new worker")
                free_vm = self.discover_free_vm()
                if free_vm:
                    await self.deploy_worker(free_vm)

        if healthy_workers < min_workers:
            logger.warning(f"Not enough healthy workers, expected at least {min_workers}, found {healthy_workers}")
            for _ in range(min_workers - healthy_workers):
                free_vm = self.discover_free_vm()
                if free_vm:
                    await self.deploy_worker(free_vm)
        elif healthy_workers > max_workers:
            logger.warning(f"Too many healthy workers, expected at most {max_workers}, found {healthy_workers}")
            for _ in range(healthy_workers - max_workers):
                worker_to_remove = self.select_healthy_worker_to_remove()
                if worker_to_remove:
                    await self.remove_worker(worker_to_remove)
        else:
            logger.info(f"Healthy workers within limits, current count: {healthy_workers}")

    def is_app_healthy(self, worker_name: str) -> bool:
        return self.workers_data[worker_name].get("status") == "healthy"

    def is_app_failed_worker_running(self, worker_name: str) -> bool:
        return self.workers_data[worker_name].get("status") == "app_failed_worker_running"

    async def update_worker_data(self, worker: dict) -> None:
        async with self.worker_operation_lock:
            try:
                async with self.session.get(f"http://{worker['host']}:{self.worker_port}/status") as response:
                    data = await response.json()
                    if response.status == 200:
                        await self.set_worker_data(worker["name"], data)
                        logger.info(f"Updated worker {worker['name']} status to {data.get('status')}")
                    else:
                        await self.set_worker_value_data(worker["name"], "status", "app_failed_worker_running")
                        logger.warning(f"Failed to update worker {worker['name']} status: {response.status}")
            except Exception as e:
                await self.set_worker_value_data(worker["name"], "status", "failed")
                logger.error(f"Error updating worker {worker['name']} status: {e}")

    def discover_free_vm(self) -> str:
        worker_hosts = {worker_data["host"] for worker_data in self.workers_data.values()}
        free_vm = next((vm for vm in self.virtual_machines if vm not in worker_hosts), None)
        logger.info(f"Discovered free VM: {free_vm}")
        return free_vm

    async def _deploy_worker_to_host(self, host: str, worker_name: str) -> None:
        credentials = f"{self.ssh_user}@{host}"
        async with self.worker_operation_lock:
            commands = [
                ("scp", "./deploy_worker.sh", f"{credentials}:./deploy_worker.sh"),
                ("ssh", credentials, "chmod", "+x", "./deploy_worker.sh"),
                ("ssh", credentials, "./deploy_worker.sh", self.worker_git_repo, worker_name, self.worker_port, self.app_image,
                 self.app_git_repo, self.app_port, self.healthcheck_api, self.app_dockerfile, self.worker_dockerfile)
            ]

            for cmd in commands:
                proc = await asyncio.create_subprocess_exec(*cmd, stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await proc.communicate()

                if proc.returncode != 0:
                    error_message = stderr.decode() if stderr else "Unknown error"
                    logger.error(f"Error executing command {' '.join(cmd)}: {error_message}")
                    raise Exception(f"Error executing command {' '.join(cmd)}: {error_message}")

            logger.info(f"Worker {worker_name} deployed to host {host}")

    async def deploy_worker(self, host: str) -> None:
        new_worker_name = f"worker-{str(uuid.uuid4())}"
        await self._deploy_worker_to_host(host, new_worker_name)
        try:
            await self.start_app(new_worker_name, host)
        except:
            logger.error(f"Failed started app on host {host} and worker_name {new_worker_name}")

    async def start_app(self, worker_name, host):
        async with self.worker_operation_lock:
            async with self.session.post(f"http://{host}:{self.worker_port}/start_app") as response:
                if response.status == 200:
                    logger.info(f"Successfully started app on host {host} and worker_name {worker_name}")
                    await self.set_worker_data(worker_name, {"name": worker_name, "host": host})
                    logger.info(f"New worker {worker_name} deployed on {host}")
                else:
                    logger.error(f"Failed started app on host {host} and worker_name {worker_name}")

    async def restart_worker(self, worker_name: str) -> None:
        worker_host = self.workers_data[worker_name]["host"]
        await self.remove_worker(worker_name)
        try:
            await self._deploy_worker_to_host(worker_host, worker_name)
            logger.info(f"Worker {worker_name} restarted on {worker_host}")
        except Exception as e:
            logger.error(f"Error restarting worker {worker_name} on {worker_host}: {str(e)}")
            raise

    async def initialize_workers_data(self) -> None:
        async with self.worker_operation_lock:
            logger.info("Initializing worker data")
            for vm in self.virtual_machines:
                worker_status_url = f"http://{vm}:{self.worker_port}/status"

                try:
                    async with self.session.get(worker_status_url) as response:
                        worker_status = await response.json()
                        worker_name = worker_status.get("worker_name")
                        worker_status = worker_status.get("status")
                        memory_usage = worker_status.get("memory_usage")
                        cpu_usage = worker_status.get("cpu_usage")

                        if worker_name and worker_status:
                            await self.set_worker_data(worker_name, {
                                "name": worker_name,
                                "host": vm,
                                "status": worker_status,
                                "memory_usage": memory_usage,
                                "cpu_usage": cpu_usage,
                            })
                            logger.info(f"Worker {worker_name} initialized with status {worker_status} on {vm}")
                except Exception as e:
                    logger.warning(f"Failed to initialize worker data for VM {vm}: {e}")
                    continue

    def select_healthy_worker_to_remove(self) -> str:
        healthy_worker = next((worker_name for worker_name, worker_data in self.workers_data.items() if
                               worker_data["status"] == "healthy"), None)
        if healthy_worker:
            logger.info(f"Selected healthy worker {healthy_worker} to remove")
        else:
            logger.warning("No healthy worker found to remove")
        return healthy_worker

    async def remove_worker(self, worker_name: str) -> None:
        async with self.worker_operation_lock:
            worker_data = self.workers_data.get(worker_name)
            if worker_data:
                host = worker_data["host"]
                stop_app_url = f"http://{host}:{self.worker_port}/stop_app"

                # Send API request to stop the application
                async with self.session as session:
                    try:
                        async with session.post(stop_app_url) as response:
                            if response.status != 200:
                                raise Exception(
                                    f"Error stopping the application on worker {worker_name} at {host}: {await response.text()}")

                        logger.info(f"Application stopped on worker {worker_name} at {host}")
                    except Exception as e:
                        logger.error(f"Error stopping the application on worker {worker_name} at {host}: {str(e)}")
                        raise

                # Stop and delete the worker container
                credentials = f"{self.ssh_user}@{host}"
                remove_process = await asyncio.create_subprocess_exec("ssh", credentials, "docker", "rm", "-f", worker_name,
                                                                      stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await remove_process.communicate()

                if remove_process.returncode != 0:
                    error_message = stderr.decode() if stderr else "Unknown error"
                    logger.error(f"Error removing worker {worker_name} from {host}: {error_message}")
                    raise Exception(f"Error removing worker {worker_name} from {host}: {error_message}")

                logger.info(f"Worker {worker_name} removed from {host}")

                await self.del_worker_data(worker_name)
            else:
                logger.warning(f"Worker {worker_name} not found for removal")
