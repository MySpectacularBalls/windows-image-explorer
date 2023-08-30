import time

import transformers
from library import utils
from library.exceptions import *
from loguru import logger
from models.object import Object, ObjectDefinition
from PIL import Image

from processor import BaseProcessor


class ImageProcessor(BaseProcessor):
    def __init__(self) -> None:
        super().__init__(
            id="image",
            type="image",
            title="Image Captioning",
            description="Generate a text that describes the provided image.",
        )

        self.config = self.get_config()

        self.processor = transformers.BlipProcessor.from_pretrained(self.config.model)
        self.model = transformers.BlipForConditionalGeneration.from_pretrained(
            self.config.model
        )
        if self.config.gpu:
            self.model = self.model.to("cuda")  # type: ignore

    def process(self, object: Object) -> ObjectDefinition:
        """
        Generate a object definition that contains a description of the provided image
        object.
        """

        self.verify_object(object)

        st = time.perf_counter()

        img = Image.open(str(object.path)).convert("RGB")

        # Generate the caption
        inputs = self.processor(img, return_tensors="pt")
        if self.config.gpu:
            inputs = inputs.to("cuda")
        output = self.model.generate(**inputs)  # type: ignore

        caption = self.processor.decode(output[0], skip_special_tokens=True)

        tt = time.perf_counter() - st

        message = f"Generated image caption of '{caption}' for object '{object}'."
        logger.info(message)

        utils.log_time_metric(
            type="generate-image-caption",
            tt=tt,
            title="Generated image caption",
            message=message,
        )

        return ObjectDefinition.create(
            type="image-description",
            content=caption,
            tt=tt,
            model=self.config.model,
            object=object,
        )


def setup():
    return ImageProcessor()
