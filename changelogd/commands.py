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
    **options: typing.Optional[str]
) -> None:
    """Initialize changelogd config."""
    config.init(path)


@command_decorator
@click.argument("version")
def draft(
    _: click.core.Context, config: Config, version: str, **options: typing.Optional[str]
) -> None:
    """Generate draft changelog."""
    changelogd.draft(config, version)


@command_decorator
@click.argument("version")
def release(
    _: click.core.Context, config: Config, version: str, **options: typing.Optional[str]
) -> None:
    """Generate changelog, clear entries and make a new release."""
    changelogd.release(config, version)


@command_decorator
@click.option(
    "--check", help="Return exit code 1 if output file is different.", is_flag=True
)
def partial(
    _: click.core.Context, config: Config, check: bool, **options: typing.Optional[str]
) -> None:
    """
    Generate changelog without clearing entries, release name is taken from config file.
    """
    changelogd.release(config, version=config.partial_name, partial=True, check=check)


@command_decorator
@click.option("--type", help="Provide message type (as number or string).")
@click.option("--message", help="Changelog message.")
def entry(
    _: click.core.Context, config: Config, **options: typing.Optional[str]
) -> None:
    """Create a new changelog entry."""
    changelogd.entry(config, options)


def register_commands(cli: click.core.Group) -> None:
    commands = (init, draft, partial, release, entry)

    for command in commands:
        cli.add_command(command)
