import nox


@nox.session(python=["3.6", "3.7", "3.8"])
def tests(session):
    session.install(".[test]")
    session.run("pytest")


@nox.session
def flak8e(session):
    session.install("flake8")
    session.run("flake8", "changelogd")


@nox.session
def mypy(session):
    session.install("mypy")
    session.run("mypy", "changelogd")


@nox.session
def docs(session):
    session.install(".[docs]")
    session.run("sphinx-build", "-b", "html", "docs", "docs/_build", "-v", "-W")
