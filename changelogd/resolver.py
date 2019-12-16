import os
import sys
import typing
from pathlib import Path

import jinja2

from .config import Config


class Resolver:
    """Class responsible for resolving templates"""

    def __init__(self, config: Config):
        self._config: Config = config
        self._templates_dir: Path = config.path / "templates"

    def resolve_template(self, releases: typing.List[typing.Dict]) -> str:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self._templates_dir.as_posix()),
        )

        templates = self._get_template_file_names(
            self._templates_dir, ("entry", "main", "release"), env
        )

        for release in releases:
            groups = []
            for group_name, group in release.pop("entries", {}).items():
                groups.append(
                    {
                        "name": group_name,
                        "entries": [
                            self._resolve_entry(entry, templates.get("entry"))
                            for entry in group
                        ],
                    }
                )
                release["entry_groups"] = groups

        return ""

    def _get_template_file_names(
        self,
        templates_dir: Path,
        templates: typing.Tuple[str, ...],
        env: jinja2.Environment,
    ) -> typing.Dict[str, typing.Optional[jinja2.Template]]:
        template_files = os.listdir(templates_dir.as_posix())
        try:
            return {
                entry: env.get_template(
                    next(
                        (item for item in template_files if item.startswith(entry)),
                        entry,
                    )
                )
                for entry in templates
            }
        except jinja2.exceptions.TemplateSyntaxError as exc:
            sys.exit(f"Syntax error in template '{exc.filename}':\n\t{exc.message}")
        except jinja2.exceptions.TemplateNotFound as exc:
            sys.exit(f"Template file for '{exc.name}' not found.")

    def _resolve_entry(self, entry: typing.Dict, template: jinja2.Template):
        return template.render(**self._config.get_data(), **entry)
