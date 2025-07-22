import importlib.metadata


_DISTRIB_NAME = "{{ cookiecutter.service_name }}"

__project_name__ = importlib.metadata.distribution(_DISTRIB_NAME).name
__version__ = importlib.metadata.version(_DISTRIB_NAME)
