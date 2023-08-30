import importlib.util
import os
import time
import traceback
from typing import Optional

import peewee
from configura import config
from database import chroma
from database import embedding_function as chroma_embedding_function
from loguru import logger
from models.object import Object, ObjectDefinition
from models.query import Query, QueryResult
from processor import BaseProcessor

from library import utils


class ProcessorManager:

    """
    The class responsible for taking in objects and processing them.
    This class also takes care of querying.
    """

    def __init__(self, processors_directory: str) -> None:
        self.processors_directory = processors_directory
        self.processors: list[BaseProcessor] = []

    def query(
        self, query: str, n_results: int = 35, max_distance: Optional[float] = None
    ) -> list[tuple[Object, float]]:
        """
        Query for objects. The query function uses similarity search.

        Parameters
        ----------
        - `query` : str
            The search query.
        - `n_results` : int
            The maximum number of results to return.
        - `max_distance` : Optional[float]
            The higher the number, the more items are returned. The lower,
            the stricter the results become. Defaults to None which means to use
            `config.main.max_query_distance`.

        Returns
        -------
        `list[tuple[Object, float]]` :
            The results and the distance. Sorted by lowest distance to highest.
        """

        if max_distance is None:
            max_distance = config.main["max_query_distance"]

        logger.info(f"Querying with '{query}'. {n_results=} {max_distance=}")

        st = time.perf_counter()

        results = []
        collection = chroma.get_or_create_collection(
            "embeddings", embedding_function=chroma_embedding_function
        )
        query_result = collection.query(query_texts=[query], n_results=n_results)

        for ids, metadatas, distances in zip(
            query_result["ids"],
            query_result["metadatas"] or [],
            query_result["distances"] or [],
        ):
            for id, metadata, distance in zip(ids, metadatas, distances):
                if distance > max_distance:  # type: ignore
                    continue

                logger.debug(f"Fetching object with ID of '{id}'.")

                try:
                    obj = Object.get(Object.id == id)
                    results.append((obj, distance))
                except peewee.DoesNotExist:
                    message = f"Object with ID of '{id}' does not exist."

                    utils.log_error(
                        type="object-not-found-while-querying",
                        title="Object not found while querying",
                        message=message,
                        metadata={"id": id, **metadata},
                    )

                    logger.error(message)
                    continue

        # Save the query data
        saved_query = Query.create(
            query=query,
            n_results=n_results,
            max_distance=max_distance,
            returned_results=len(results),
        )
        for result in results:
            QueryResult.create(query=saved_query, object=result[0], distance=result[1])

        tt = time.perf_counter() - st
        logger.info(
            f"Query took {round(tt, 2)}s and returned {len(results)} result(s)."
        )
        utils.log_time_metric(
            type="query",
            tt=tt,
            title="Query objects",
            message=f"Queried objects with query string '{query}'.",
        )

        return results

    def generate_embeddings(
        self, object: Object, definitions: list[ObjectDefinition]
    ) -> None:
        """
        Generate embeddings for the provided object and object definitions.

        Parameters
        ----------
        - `object` : Object
            The object to generate embeddings for.
        - `definitions` : list[ObjectDefinition]
            A list of definitions associated with the object.
        """

        logger.info(
            f"Generating embeddings for object '{object}' and its {len(definitions)} definition(s)."
        )

        st = time.perf_counter()

        documents = [f"File name: {object.name}", f"File path: {object.path}"]
        for definition in definitions:
            documents.append(str(definition.content))

        text = "\n".join(documents)

        collection = chroma.get_or_create_collection(
            "embeddings", embedding_function=chroma_embedding_function
        )
        collection.add(
            documents=[text],
            ids=[str(object.id)],
            metadatas=[
                {
                    "path": str(object.path),
                    "name": str(object.name),
                    "file_id": str(object.file_id),
                }
            ],
        )

        # Update the object in the database
        Object.update(generated_embeddings=True).where(Object.id == object.id).execute()

        tt = time.perf_counter() - st
        message = f"Generated embeddings in {round(tt, 2)}s for object '{object}' with {len(definitions)} definition(s)."

        utils.log_time_metric(
            type="generate-embeddings",
            tt=tt,
            title=f"Generated embeddings for object '{object}'",
            message=message,
        )

        logger.info(message)

    def process(self, object: Object) -> list[ObjectDefinition]:
        """
        Process a object with the right processors. Once processed, the object is
        marked as processed.

        Parameters
        ----------
        - `object` : Object
            The unprocessed object.

        Returns
        -------
        `list[ObjectDefinition]` :
            A list of generated object definitions.
        """

        logger.info(f"Processing object '{object}'.")

        definitions = []
        valid_processors = [x for x in self.processors if x.type == object.type]
        success = False

        for processor in valid_processors:
            logger.debug(f"Running processor '{processor.title}' on '{object}'.")

            try:
                definition = processor.process(object)
                logger.debug(f"Processor result: '{definition}'.")
                definitions.append(definition)
                success = True
            except Exception:
                logger.exception(f"Error processing object '{object}'.")

                utils.log_error(
                    type="processing-object-failed",
                    title=f"Processing object '{object}' failed.",
                    message=f"A unknown error has occurred while calling the `processor.process` method on the object '{object}'.",
                    metadata={"object_id": str(object.id), "processor": processor.id},
                )

                Object.update(error=True, error_traceback=traceback.format_exc()).where(
                    Object.id == object.id
                ).execute()

                success = False

        if success:
            Object.update(processed=True).where(Object.id == object.id).execute()

        return definitions

    def load_processor(self, file_name: str) -> Optional[BaseProcessor]:
        """
        Attempts to load the provided file (without an extension) as a processor.
        This method can raise exceptions if loading the processor fails.

        Parameters
        ----------
        `file_name` : str
            The name of the processor file (with no extension) under the processor
            directory.

        Returns
        -------
        `BaseProcessor` :
            The processor.
        """

        logger.info(f"Loading processor '{file_name}'.")

        path = os.path.join(self.processors_directory, f"{file_name}.py")
        spec = importlib.util.spec_from_file_location(file_name, path)
        if spec is None:
            return

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore

        return module.setup()

    def load_processors(self) -> list[BaseProcessor]:
        """
        Load all the processors in the processor directory.
        """

        logger.info("Loading processors...")
        i = 0
        failed = []
        success = []

        for file in os.listdir(self.processors_directory):
            if not file.endswith(".py"):
                continue

            if file in ("__init__.py"):
                continue

            i += 1

            name = os.path.splitext(file)[0]
            processor = self.load_processor(name)
            if processor is None:
                failed.append(name)
                logger.error(f"Loading '{name}' failed.")
            else:
                success.append(processor)
                logger.debug(f"Successfully loaded '{name}'.")

        logger.info(f"Successfully loaded {len(success)}/{i} processor(s).")

        self.processors = success
        return success


processor_manager = ProcessorManager(os.path.join(os.getcwd(), "processor"))
