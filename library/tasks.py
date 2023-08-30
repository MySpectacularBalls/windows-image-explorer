import multiprocessing
import os
import random
import signal
import threading
import time
import traceback
from multiprocessing.synchronize import Event as EventClass
from typing import Optional, Union

import peewee as pw
from configura import config
from loguru import logger
from models.object import IgnoredFile, Object, ObjectDefinition
from PIL import Image

from library import processor_manager, utils
from library.exceptions import *


class TaskManager:
    def __init__(self) -> None:
        self.events: dict[int, Union[EventClass, threading.Event]] = {}

    def stop(self) -> None:
        for event in self.events.values():
            event.set()

        logger.info("Tasks are stopping...")

    def start(self) -> None:
        """
        Start the indefinite running tasks in the background.
        """

        last_id = 0
        processes = (
            []
        )  # Put indefinite tasks that should run in a separate process here
        for process_id, process_function in enumerate(processes):
            event = multiprocessing.Event()
            process = multiprocessing.Process(target=process_function, args=(event,))

            self.events[process_id] = event

            logger.debug(f"Starting process '{process_function.__name__}'.")
            process.start()
            last_id = process_id

        threads = [
            self._generate_embeddings_for_object,
            self._process_random_object,
            self._scan_objects,
        ]  # Put indefinite tasks that should run in a different thread here
        for thread_id, thread_function in enumerate(threads, start=last_id + 1):
            event = threading.Event()
            thread = threading.Thread(
                target=thread_function, args=(event,), daemon=True
            )

            self.events[thread_id] = event

            logger.debug(f"Starting thread '{thread_function.__name__}'.")
            thread.start()
            last_id = thread_id

        logger.debug("Tasks started.")

    def _generate_embeddings_for_object(self, event: EventClass) -> None:
        """
        Start generating embeddings for all objects.
        """

        def get_object_and_definitions() -> (
            Optional[tuple[Object, list[ObjectDefinition]]]
        ):
            query = (
                (Object.generated_embeddings == False)
                & (Object.error == False)
                & (Object.processed == True)
            )
            count = Object.select().where(query).count()
            if count == 0:
                return

            object = (
                Object.select().where(query).order_by(pw.fn.Random()).limit(1).first()
            )
            definitions = object.definitions
            return object, definitions

        while not event.is_set():
            # Get a object and its definitions
            query_result = get_object_and_definitions()
            if query_result is None:
                time.sleep(1)
                continue

            object, definitions = query_result
            processor_manager.generate_embeddings(
                object=object, definitions=definitions
            )
            time.sleep(0.7)

    def _process_random_object(self, event: EventClass) -> None:
        """
        Process a random unprocessed object from the database.
        """

        processor_manager.load_processors()

        def get_random_unprocessed_object() -> Optional[Object]:
            query = (
                (Object.processed == False)
                & (Object.error == False)
                & (Object.generated_embeddings == False)
            )
            count = Object.select().where(query).count()
            if count == 0:
                return

            return (
                Object.select().where(query).order_by(pw.fn.Random()).limit(1).first()
            )

        while not event.is_set():
            # Get a random object
            object = get_random_unprocessed_object()
            if object is None:
                time.sleep(1)
                continue

            processor_manager.process(object)

    def _scan_objects(self, event: EventClass) -> None:
        """
        Scan the device for potential objects and save them to the database.
        """

        while not event.is_set():
            st = time.perf_counter()

            logger.info("Scanning objects to save.")

            # Gather all valid file extensions
            file_extensions = []
            for type in config.types:
                file_extensions.extend(type["file_extensions"])
            file_extensions = tuple(file_extensions)

            files_saved = 0
            files_duplicate = 0

            try:
                for drive in utils.get_drives():
                    for root, dirs, files in os.walk(drive):
                        if event.is_set():
                            raise StopException

                        dirs[:] = [
                            d for d in dirs if d not in config.ignored_directories
                        ]

                        for file in files:
                            if not file.lower().endswith(file_extensions):
                                continue

                            path = os.path.join(root, file)
                            file_id = utils.get_file_id(path)
                            if (
                                not Object.select(pw.fn.COUNT(Object.id))
                                .where(Object.file_id == file_id)
                                .scalar()
                            ) and (
                                not IgnoredFile.select()
                                .where(IgnoredFile.file_id == file_id)
                                .count()
                            ):
                                ignore = False
                                ignore_type = "invalid-file"
                                try:
                                    obj = Object.from_path(path)
                                    if obj:
                                        files_saved += 1
                                    else:
                                        ignore = True
                                except Image.DecompressionBombError:
                                    logger.exception("Decompression Bomb Error.")
                                    utils.log_error(
                                        type="decompression-bomb-error",
                                        title="Decompression Bomb Error",
                                        message=f"A decompression bomb error has occurred while trying to create an object from the path '{path}'.",
                                        traceback=traceback.format_exc(),
                                        metadata={"path": path},
                                    )
                                    ignore = True
                                    ignore_type = "decompression-bomb-error"

                                if ignore:
                                    logger.info(
                                        f"Adding '{path}' to ignored file list because of '{ignore_type}'."
                                    )
                                    IgnoredFile.create(
                                        file_id=file_id, type=ignore_type
                                    )
                            else:
                                files_duplicate += 1

            except StopException:
                logger.info("Stopping objects scanner...")
                break
            except Exception:
                logger.exception("Error scanning objects.")

            tt = round(time.perf_counter() - st, 2)

            # Log summary
            logger.info(f"{files_saved} File(s) saved.")
            logger.info(f"{files_duplicate} Duplicate(s) found and ignored.")
            logger.info(f"Completion time: {tt} seconds.")

            time.sleep(30)


task_manager = TaskManager()
