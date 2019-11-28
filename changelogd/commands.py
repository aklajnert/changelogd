import typing

import click

from . import changelogd
from .config import Config


def command_decorator(func: typing.Callable) -> click.core.Command:
    pass_state = click.make_pass_decorator(Config, ensure=True)
    verbose = click.option(
        *("-v", "--verbose"),
        count=True,
        help="Increase verbosity.",
        callback=Config.set_verbosity  # type: ignore
    )
    return click.command()(verbose(pass_state(click.pass_context(func))))


@command_decorator
@click.option(*("-p", "--path"), help="Custom configuration directory")
def init(
    _: click.core.Context,
    config: Config,
    path: typing.Optional[str],
    **options: typing.Dict[str, typing.Any]
) -> None:
    """Initialize changelogd config."""
    config.init_config(path)


@command_decorator
@click.argument("version")
def draft(
    _: click.core.Context,
    config: Config,
    version: str,
    **options: typing.Dict[str, typing.Any]
) -> None:
    """Generate draft changelog."""
    changelogd.prepare_draft(config, version)


@command_decorator
def release(
    _: click.core.Context, config: Config, **options: typing.Dict[str, typing.Any]
) -> None:
    """Generate changelog, clear entries and make a new release."""
    print("release")


@command_decorator
def entry(
    _: click.core.Context, config: Config, **options: typing.Dict[str, typing.Any]
) -> None:
    """Create a new changelog entry."""
    changelogd.create_entry(config)


def register_commands(cli: click.core.Group) -> None:
    commands = (init, draft, release, entry)

    for command in commands:
        cli.add_command(command)
