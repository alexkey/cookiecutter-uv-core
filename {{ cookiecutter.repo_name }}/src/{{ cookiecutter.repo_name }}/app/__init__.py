from importlib.metadata import metadata

_DISTRIB_NAME = "{{ cookiecutter.service_name }}"
_meta = metadata(_DISTRIB_NAME)

__project_name__ = _meta["Name"]
__version__ = _meta["Version"]
