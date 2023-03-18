import os
import tempfile
import logging

import docker
import requests
from git import Repo

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class AppRunner:
    def __init__(
        self, app_image, app_port, healthcheck_api, app_dockerfile, app_git_repo
    ):
        self.app_image = app_image
        self.app_port = app_port
        self.healthcheck_api = healthcheck_api
        self.app_dockerfile = app_dockerfile
        self.app_git_repo = app_git_repo
        self.client = docker.from_env()
        self.container = None

    def start(self):
        logging.info("Starting the app")

        existing_container = self.get_existing_container()
        if existing_container:
            logging.info(
                f"Container with name {self.app_image} already exists. Stopping and removing ..."
            )
            existing_container.stop()
            existing_container.wait()
            existing_container.remove()

        self.build_image()

        self.container = self.client.containers.run(
            self.app_image,
            name=self.app_image,
            detach=True,
            ports={f"{self.app_port}/tcp": self.app_port},
        )

    def build_image(self):
        logging.info("Building the app image...")
        with tempfile.TemporaryDirectory() as tempdir:
            self._clone_repo(tempdir)
            build_context = os.path.dirname(os.path.join(tempdir, self.app_dockerfile))
            dockerfile = os.path.basename(self.app_dockerfile)
            logging.info(
                f"Build context for app image is {build_context}, dockerfile is {dockerfile}"
            )
            self.client.images.build(
                path=build_context, tag=self.app_image, dockerfile=dockerfile, rm=True
            )

    def _clone_repo(self, tempdir):
        logging.info(f"Cloning the app git repo {self.app_git_repo}")
        remote_repo = Repo.clone_from(self.app_git_repo, tempdir)
        logging.info(f"Git repository cloned to {tempdir}")
        logging.info("Listing content of the cloned repository:")
        for item in os.listdir(tempdir):
            logging.info(f"  - {item}")
        return remote_repo

    def get_existing_container(self, only_running: bool = False):
        logging.info(
            f"Checking for existing running container with name {self.app_image}"
        )
        containers = self.client.containers.list(
            filters={"name": self.app_image}, all=not only_running
        )
        if containers:
            logging.info(f"Container with name {self.app_image} exists")
            return containers[0]
        return None

    def stop(self):
        logging.info("Stopping the app container")
        container = self.get_existing_container()
        if container:
            logging.info(f"Container with name {self.app_image} will be stopped")
            container.stop()
            container.wait()
            logging.info(f"Container with name {self.app_image} stopped")
            self.container = None

    def get_status(self):
        logging.info("Getting the app status")
        if self.healthcheck_api:
            try:
                response = requests.get(
                    f"http://localhost:{self.app_port}{self.healthcheck_api}", timeout=5
                )
                if response.status_code == 200:
                    logging.info(f"App healthcheck OK")
                    return "healthy"
                else:
                    logging.info(f"App healthcheck FAIL")
                    return "app_failed_worker_running"
            except (requests.exceptions.RequestException, requests.exceptions.Timeout):
                logging.info(f"App healthcheck FAIL. Trying check running container")

        if self.get_existing_container(only_running=True):
            logging.info(f"App healthcheck OK")
            return "healthy"
        else:
            logging.info(f"App healthcheck FAIL")
            return "app_failed_worker_running"

    def get_memory_usage(self):
        if not self.container:
            logging.info(f"Memory usage empty")
            return 0

        stats = self.container.stats(stream=False)
        memory_stats = stats.get("memory_stats", {})
        memory_usage = memory_stats.get("usage", 0)
        logging.info(f"Memory usage {memory_usage}")
        total_memory = memory_stats.get("limit", 1)

        logging.info(f"Memory limit {total_memory}")

        memory_usage_percent = (memory_usage / total_memory) * 100
        logging.info(f"Memory usage percent usage/limit {memory_usage_percent}%")
        return memory_usage_percent

    def get_cpu_usage(self):
        if not self.container:
            logging.info(f"CPU usage empty")
            return 0

        stats = self.container.stats(stream=False)
        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})
        cpu_usage = cpu_stats.get("cpu_usage", {})
        precpu_usage = precpu_stats.get("cpu_usage", {})

        cpu_delta = cpu_usage.get("total_usage", 0) - precpu_usage.get("total_usage", 0)
        system_cpu_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get(
            "system_cpu_usage", 0
        )

        if system_cpu_delta > 0 and cpu_delta > 0:
            cpu_usage_percent = (
                (cpu_delta / system_cpu_delta)
                * len(cpu_usage.get("percpu_usage", []))
                * 100
            )
            logging.info(f"CPU usage {cpu_usage_percent}%")
            return cpu_usage_percent

        logging.info(f"CPU usage empty")
        return 0
