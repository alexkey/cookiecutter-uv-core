import importlib.metadata


_distribution_name = "{{ cookiecutter.service_name }}"

__name__ = importlib.metadata.distribution(_distribution_name).name
__version__ = importlib.metadata.version(_distribution_name)
