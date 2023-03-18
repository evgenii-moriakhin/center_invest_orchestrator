import os
from flask import Flask, jsonify, make_response
from app_runner import AppRunner

app = Flask(__name__)


class Worker:
    def __init__(
        self,
        worker_name,
        app_image,
        app_port,
        healthcheck_api,
        app_dockerfile,
        app_git_repo,
    ):
        self.worker_name = worker_name
        self.app_image = app_image
        self.app_port = app_port
        self.healthcheck_api = healthcheck_api
        self.app_dockerfile = app_dockerfile
        self.app_git_repo = app_git_repo
        self.app_runner = AppRunner(
            self.app_image,
            self.app_port,
            self.healthcheck_api,
            self.app_dockerfile,
            self.app_git_repo,
        )

    def start_app(self):
        self.app_runner.start()

    def stop_app(self):
        self.app_runner.stop()

    def get_status(self):
        return {
            "worker_name": self.worker_name,
            "status": self.app_runner.get_status(),
            "memory_usage": self.app_runner.get_memory_usage(),
            "cpu_usage": self.app_runner.get_cpu_usage(),
        }


worker = Worker(
    worker_name=os.environ["WORKER_NAME"],
    app_image=os.environ["APP_IMAGE"],
    app_port=os.environ["APP_PORT"],
    healthcheck_api=os.environ["HEALTHCHECK_API"],
    app_dockerfile=os.environ["APP_DOCKERFILE"],
    app_git_repo=os.environ["APP_GIT_REPO"],
)


@app.route("/status", methods=["GET"])
def status():
    status_ = worker.get_status()
    return jsonify(status_)


@app.route("/stop_app", methods=["POST"])
def stop_app():
    worker.stop_app()
    return make_response(jsonify({"message": "App stopped successfully"}), 200)


@app.route("/start_app", methods=["POST"])
def start_app():
    worker.start_app()
    return make_response(jsonify({"message": "App started successfully"}), 200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ["WORKER_PORT"]))
