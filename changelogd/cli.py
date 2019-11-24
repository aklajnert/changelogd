# -*- coding: utf-8 -*-
"""Console script for changelogd."""
import sys

import click

from . import __version__
from .commands import register_commands


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(_) -> None:
    """Changelogs without conflicts."""


def main() -> None:
    """Entrypoint function."""
    register_commands(cli)
    cli(prog_name="changelogd", obj={}, max_content_width=100)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
