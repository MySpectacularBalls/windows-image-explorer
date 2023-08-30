class InvalidObjectType(Exception):
    def __init__(self, expected: str, provided: str) -> None:
        self.expected = expected
        self.provided = provided

        super().__init__(f"Expected '{self.expected}' but got '{self.provided}'.")


class StopException(Exception):
    ...
