import nox

nox.options.sessions = ["tests", "flake8", "mypy", "docs"]


@nox.session(python=["3.6", "3.7", "3.8", "3.9", "3.10", "3.11", "3.12"])
def tests(session):
    session.install(".[test]")
    session.run("pytest")


@nox.session
def flake8(session):
    session.install("flake8")
    session.run("flake8", "changelogd")


@nox.session
def mypy(session):
    session.install("mypy", "types-click", "types-jinja2")
    session.run("mypy", "changelogd")


@nox.session
def docs(session):
    session.install(".[docs]")
    session.run("sphinx-build", "-b", "html", "docs", "docs/_build", "-v", "-W")


@nox.session
def create_dist(session):
    session.install("twine")
    session.run("python", "setup.py", "sdist", "bdist_wheel")
    session.run("twine", "check", "dist/*")


@nox.session
def publish(session):
    """Publish to pypi. Run `nox publish -- prod` to publish to the official repo."""
    create_dist(session)
    twine_command = ["twine", "upload", "dist/*"]
    if "prod" not in session.posargs:
        twine_command.extend(["--repository-url", "https://test.pypi.org/legacy/"])
    session.run(*twine_command)
