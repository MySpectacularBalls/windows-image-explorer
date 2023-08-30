import dataclasses
import json
import os
from abc import ABC, abstractmethod
from typing import Optional

from library.exceptions import *
from library.types import ObjectType
from models.object import Object, ObjectDefinition


@dataclasses.dataclass
class ProcessorConfig:

    """
    Contains configuration about a specific processor.
    """

    model: str
    gpu: bool = False
    enabled: bool = True


class ProcessorABC(ABC):
    @abstractmethod
    def process(self, object: Object) -> ObjectDefinition:
        """
        Process the object and create a definition for the object.
        """


class BaseProcessor(ProcessorABC):

    """
    The base processor that every processor must derive from.

    Attributes
    ----------------
    - `id` : str
        The ID of the processor. This should be the processor's file name without the .py
        extension.
    - `type` : ObjectType
        What object type should the processor target.
    - `title` : str
        The title of the processor. Used for metadata purposes.
    - `description` : str
        The description of the processor. Used for metadata purposes.
    """

    def __init__(
        self,
        id: str,
        type: ObjectType,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        self.id = id
        self.type = type

        # Metadata
        self.title = title
        self.metadata = description

    def get_config(self) -> ProcessorConfig:
        """
        Return the config file for this processor
        """

        with open(
            os.path.join(os.getcwd(), "processor", f"{self.id}.json"), encoding="utf-8"
        ) as f:
            return ProcessorConfig(**json.load(f))

    def set_config(self, config: ProcessorConfig) -> ProcessorConfig:
        """
        Set the content of the config. This is a dangerous function as it completely
        overwrites the contents of the `.json` config file. Ensure that the format
        matches exactly with the `ProcessorConfig` dataclass.
        """

        data = dataclasses.asdict(config)

        with open(
            os.path.join(os.getcwd(), "processor", f"{self.id}.json"), encoding="utf-8"
        ) as f:
            json.dump(data, f, indent=2)
            return config

    def verify_object(self, object: Object) -> None:
        """
        Verifies if the object is fit for this processor. An error is raised if it isn't.
        """

        if object.type != self.type:
            raise InvalidObjectType(self.type, str(object.type))
