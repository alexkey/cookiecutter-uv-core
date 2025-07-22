from {{ cookiecutter.repo_name }}.app import (
    __project_name__,
    __version__,
)


def main() -> None:
    print(f"Welcome to {__project_name__} version {__version__}")
