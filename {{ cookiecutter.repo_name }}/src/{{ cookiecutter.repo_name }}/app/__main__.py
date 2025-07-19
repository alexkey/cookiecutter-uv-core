from {{ cookiecutter.repo_name }}.app import (
    __name__,
    __version__,
)


def main() -> None:
    print(f"Welcome to {__name__} version {__version__}")
