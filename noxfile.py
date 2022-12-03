import nox


@nox.session
def ruff(session: nox.Session):
    session.install("ruff")
    session.run("ruff", ".")


@nox.session
def black(session: nox.Session):
    session.install("black")
    session.run("black", ".", "--check")
