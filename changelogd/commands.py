import click


@click.command()
@click.pass_context
def init(_) -> None:
    """Initialize changelogd config."""
    print("config")


@click.command()
@click.pass_context
def draft(_) -> None:
    """Generate draft changelog."""
    print("draft")


@click.command()
@click.pass_context
def release(_) -> None:
    """Generate changelog, clear entries and make a new release."""
    print("release")


@click.command()
@click.pass_context
def entry(_) -> None:
    """Create a new changelog entry."""
    print("entry")


def register_commands(cli: click.core.Group) -> None:
    commands = (init, draft, release, entry)

    for command in commands:
        cli.add_command(command)
