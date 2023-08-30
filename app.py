import logging
import os
import sys
from importlib import import_module

from configura import config
from flask import Flask
from loguru import logger

from library import task_manager

logger.remove()
logger.add(sys.stderr, level="DEBUG", enqueue=True)

logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)
logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.INFO)
logging.getLogger("peewee").setLevel(logging.INFO)
logging.getLogger("PIL.Image").setLevel(logging.INFO)


class Main:
    def __init__(self) -> None:
        self.app = Flask(__name__)

    def register_blueprints(self) -> None:
        """
        Register all blueprints in the `blueprints` directory.
        """

        for file in os.listdir(os.path.join(os.getcwd(), "blueprints")):
            if not file.endswith(".py") or file in ("__init__.py"):
                continue

            module = import_module(f"blueprints.{file[:-3]}")
            blueprint = module.setup()
            self.app.register_blueprint(blueprint)

            logger.info(f"Registered blueprint {file}.")

    def start(self) -> None:
        """
        Starts windows image explorer.
        """

        logger.info("Starting windows image explorer...")
        self.register_blueprints()
        task_manager.start()

        self.app.run(
            host=config.main["server"]["host"],
            port=config.main["server"]["port"],
            debug=not config.main["production"],
            use_reloader=False,
        )

        task_manager.stop()


if __name__ == "__main__":
    main = Main()
    main.start()
