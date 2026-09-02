from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class IncludeLoader(yaml.SafeLoader):
    def __init__(self, stream) -> None:
        self.root = Path(getattr(stream, "name", ".")).resolve().parent
        super().__init__(stream)


def _include(loader: IncludeLoader, node: yaml.Node) -> Any:
    path = loader.root / loader.construct_scalar(node)
    with path.open(encoding="utf-8") as handle:
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.load(handle, IncludeLoader)
        if path.suffix.lower() == ".json":
            return json.load(handle)
        return handle.read()


IncludeLoader.add_constructor("!include", _include)


class QuotedDumper(yaml.SafeDumper):
    pass


def _quoted_string(dumper: QuotedDumper, value: str):
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style='"')


QuotedDumper.add_representer(str, _quoted_string)


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.load(handle, IncludeLoader)


def dump_yaml(value: Any) -> str:
    return yaml.dump(value, Dumper=QuotedDumper, allow_unicode=True, default_flow_style=False)
