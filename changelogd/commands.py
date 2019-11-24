import click


def command_decorator(func: callable) -> click.core.Command:
    verbose = click.option("-v", "--verbose", count=True, help="Increase verbosity.")
    return verbose(click.command()(click.pass_context(func)))


@command_decorator
def init(_: click.core.Context, verbose: int) -> None:
    """Initialize changelogd config."""
    print("config", verbose)


@command_decorator
def draft(_: click.core.Context, verbose: int) -> None:
    """Generate draft changelog."""
    print("draft", verbose)


@command_decorator
def release(_: click.core.Context, verbose: int) -> None:
    """Generate changelog, clear entries and make a new release."""
    print("release", verbose)


@command_decorator
def entry(_: click.core.Context, verbose: int) -> None:
    """Create a new changelog entry."""
    print("entry", verbose)


def register_commands(cli: click.core.Group) -> None:
    commands = (init, draft, release, entry)

    for command in commands:
        cli.add_command(command)
