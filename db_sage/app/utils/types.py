from dataclasses import dataclass, field
from typing import List


@dataclass
class TurboTool:
    """Represents a TurboTool with a name, configuration, and function.

    Attributes:
        name (str): The name of the TurboTool.
        config (dict): The configuration of the TurboTool.
        function (callable): The function that the TurboTool executes.
    """
    name: str
    config: dict
    function: callable