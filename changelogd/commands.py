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
        callback=Config.set_verbosity,  # type: ignore
    )
    return click.command()(verbose(pass_state(click.pass_context(func))))


def dynamic_options(func: typing.Callable) -> typing.Callable:
    output = click.option("--type", help="Message type (as number or string).")(func)
    try:
        entry_fields = Config().get_value("entry_fields")
    except SystemExit:
        return output
    for entry_field in entry_fields:
        name = entry_field.get("name").replace("_", "-")
        if not name or " " in name:
            continue
        kwargs = dict()
        verbose_name = entry_field.get("verbose_name")
        if verbose_name:
            kwargs["help"] = verbose_name

        output = click.option(f"--{name}", **kwargs)(output)
    return output


@command_decorator
@click.option(*("-p", "--path"), help="Custom configuration directory")
@click.option("--rst", is_flag=True, help="Use templates in RST format")
def init(
    _: click.core.Context,
    config: Config,
    path: typing.Optional[str],
    rst: bool,
    **options: typing.Optional[str],
) -> None:
    """Initialize changelogd config."""
    format = "rst" if rst else "md"
    config.init(path, format)


@command_decorator
@click.argument("version", required=False)
def draft(
    _: click.core.Context, config: Config, version: str, **options: typing.Optional[str]
) -> None:
    """Generate draft changelog to stdout."""
    if version is None:
        version = "draft"
    changelogd.draft(config, version)


@command_decorator
@click.argument("version")
@click.option(
    "--empty",
    is_flag=True,
    help="Do not crash if there are no entry files.",
)
def release(
    _: click.core.Context,
    config: Config,
    version: str,
    empty: bool = False,
    **options: typing.Optional[str],
) -> None:
    """Generate changelog, clear entries and make a new release."""
    config.settings["empty"] = empty
    changelogd.release(config=config, version=version)


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
    changelogd.release(config=config, check=check, partial=True)


@command_decorator
@dynamic_options
def entry(
    _: click.core.Context, config: Config, **options: typing.Optional[str]
) -> None:
    """Create a new changelog entry."""
    changelogd.entry(config, options)


def register_commands(cli: click.core.Group) -> None:
    commands = (init, draft, partial, release, entry)

    for command in commands:
        cli.add_command(command)
