import aiohttp
from aiohttp import web

from master.remote_workers_manager import RemoteWorkerManager


class OrchestratorAPI:
    def __init__(self, worker_manager: RemoteWorkerManager):
        self.worker_manager = worker_manager

    async def index(self, request: web.Request) -> web.Response:
        html = """
             <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Orchestrator</title>
                <!-- Add Bootstrap CSS and JS -->
                <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>
                <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
            </head>
            <body>
                <div class="container">
                    <div class="row justify-content-center mt-5">
                        <div class="col-md-8 text-center">
                            <h1 class="my-4">Orchestrator</h1>
                        </div>
                    </div>
                    <div class="row justify-content-center">
                        <div class="col-md-8">
                            <div class="card-deck">
                                <div class="card">
                                    <div class="card-body">
                                        <h5 class="card-title">Worker Statuses</h5>
                                        <p class="card-text">Check the status of workers on your system.</p>
                                        <button id="refreshWorkers" class="btn btn-primary">Refresh</button>
                                    </div>
                                </div>
                                <div class="card">
                                    <div class="card-body">
                                        <h5 class="card-title">Update Workers</h5>
                                        <p class="card-text">Force update the status of workers on your system.</p>
                                        <button id="updateWorkers" class="btn btn-secondary">Force Update</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row justify-content-center mt-4">
                        <div class="col-md-8">
                            <div class="card-deck">
                                <div class="card">
                                    <div class="card-body">
                                        <h5 class="card-title">Configurations</h5>
                                        <p class="card-text">View the configurations for your system.</p>
                                        <button id="viewConfigs" class="btn btn-info">View Configs</button>
                                    </div>
                                </div>
                                <div class="card">
                                    <div class="card-body">
                                        <h5 class="card-title">Healthy Hosts</h5>
                                        <p class="card-text">View the healthy hosts on your system.</p>
                                        <button id="viewHealthyHosts" class="btn btn-success">View Healthy Hosts</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row justify-content-center mt-5">
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Worker Status Output</h5>
                                    <pre id="workerStatusesOutput"></pre>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row justify-content-center mt-5">
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Configurations Output</h5>
                                <pre id="configsOutput"></pre>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row justify-content-center mt-5">
                    <div class="col-md-8">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Healthy Hosts Output</h5>
                                <pre id="healthyHostsOutput"></pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                async function fetchAndUpdate(url, id) {
                    const response = await fetch(url);
                    const data = await response.json();
                    document.getElementById(id).innerText = JSON.stringify(data, null, 2);
                }
            
                document.getElementById("refreshWorkers").addEventListener("click", () => {
                    fetchAndUpdate('/workers', 'workerStatusesOutput');
                });
            
                document.getElementById("updateWorkers").addEventListener("click", async () => {
                    await fetch('/workers', { method: 'PUT' });
                    fetchAndUpdate('/workers', 'workerStatusesOutput');
                });
            
                document.getElementById("viewConfigs").addEventListener("click", () => {
                    fetchAndUpdate('/settings', 'configsOutput');
                });
            
                document.getElementById("viewHealthyHosts").addEventListener("click", () => {
                    fetchAndUpdate('/healthy_hosts', 'healthyHostsOutput');
                });
            </script>
            </body>
            </html>
            """
        return web.Response(text=html, content_type="text/html")

    async def get_workers_statuses(self, request: web.Request) -> web.Response:
        worker_statuses = self.worker_manager.workers_data
        return web.json_response(worker_statuses)

    async def update_workers_data(self, request: web.Request) -> web.Response:
        # Assuming the update_workers_data method in the RemoteWorkerManager is modified to be a coroutine
        async with aiohttp.ClientSession() as session:
            for worker in self.worker_manager.workers_data.values():
                await self.worker_manager.update_worker_data(worker, session)
        return web.Response(status=204)

    async def get_hosts_with_healthy_workers(
        self, request: web.Request
    ) -> web.Response:
        healthy_hosts = [
            f"{worker_data['host']}:{self.worker_manager.app_port}"
            for worker_data in self.worker_manager.workers_data.values()
            if worker_data["status"] == "healthy"
        ]
        return web.json_response(healthy_hosts)

    async def get_master_settings(self, request: web.Request) -> web.Response:
        settings = {
            "worker_limits": self.worker_manager.worker_limits,
            "virtual_machines": self.worker_manager.virtual_machines,
            "worker_port": self.worker_manager.worker_port,
            "app_port": self.worker_manager.app_port,
            # Add other settings here
        }
        return web.json_response(settings)

    def create_app(self) -> web.Application:
        app = web.Application()
        app.add_routes(
            [
                web.get("/", self.index),
                web.get("/workers", self.get_workers_statuses),
                web.put("/workers", self.update_workers_data),
                web.get("/healthy_hosts", self.get_hosts_with_healthy_workers),
                web.get("/settings", self.get_master_settings),
            ]
        )
        return app
