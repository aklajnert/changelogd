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

    def full_resolve(self, releases: typing.List[typing.Dict]) -> str:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self._templates_dir.as_posix()),
        )

        templates = self._get_template_file_names(
            self._templates_dir, ("entry", "main", "release"), env
        )

        message_types = self._config.get_value("message_types", [])
        resolved_releases = [
            self._resolve_release(message_types, release, templates)
            for release in releases
        ]

        template = templates["main"]
        return template.render(**self._config.get_context(), releases=resolved_releases)

    def _resolve_release(
        self,
        message_types: typing.List[typing.Dict],
        release: typing.Dict,
        templates: typing.Dict[str, jinja2.Template],
    ) -> str:
        groups = {}
        for group_name, group in release.pop("entries", {}).items():
            groups[group_name] = [
                self._resolve_entry(entry, templates["entry"]) for entry in group
            ]

            release["entry_groups"] = []
            for message_type in message_types:
                name = message_type.get("name")
                title = message_type.get("title", name)

                if name in groups:
                    release["entry_groups"].append(
                        {"name": name, "title": title, "entries": groups.get(name)}
                    )

        template = templates["release"]
        return template.render(**self._config.get_context(), **release)

    def _get_template_file_names(
        self,
        templates_dir: Path,
        templates: typing.Tuple[str, ...],
        env: jinja2.Environment,
    ) -> typing.Dict[str, jinja2.Template]:
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

    def _resolve_entry(self, entry: typing.Dict, template: jinja2.Template) -> str:
        return template.render(**self._config.get_context(), **entry)
