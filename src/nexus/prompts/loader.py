from pathlib import Path


def load_prompts_dir() -> Path:
    """Return the prompts directory path."""
    return Path(__file__).parent


def load_prompt(name: str, **kwargs) -> str:
    """Load a prompt template and format it with the provided variables."""
    path = load_prompts_dir() / name
    template = path.read_text()
    if kwargs:
        return template.format(**kwargs)
    return template
