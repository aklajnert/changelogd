import logging
import subprocess
import typing


def get_git_data() -> typing.Optional[typing.Tuple[str, str]]:
    try:
        git_data = subprocess.check_output(["git", "config", "--list"])
    except subprocess.CalledProcessError:
        logging.info("Cannot read git data.")
        return None

    data = {
        key: value
        for key, value in (
            line.split("=", maxsplit=1)
            for line in git_data.decode().splitlines()
            if "=" in line
        )
    }
    return data.get("user.name", ""), data.get("user.email", "")
