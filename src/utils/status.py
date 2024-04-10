from rich.console import Console

CONSOLE = Console()
SPINNER = "dots"


def status(text: str):
    return CONSOLE.status(text, spinner=SPINNER)
