import logging
import re
import subprocess
import sys
import typing
from typing import List
from typing import Optional


def remote_branch_name() -> Optional[str]:
    """Extract remote branch name"""
    return _value_from_process(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        "remote branch name",
    )


def local_branch_name() -> Optional[str]:
    """Extract local branch name"""
    return _value_from_process(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], "local branch name"
    )


def branch_name() -> Optional[str]:
    """Extract local AND remote branch name separated by space"""
    data = []
    local = local_branch_name()
    if local:
        data.append(local)
    remote = remote_branch_name()
    if remote:
        data.append(remote)
    result = " - ".join(data)
    return result or None


def _value_from_process(
    command: List[str], error_context: Optional[str] = None
) -> Optional[str]:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    if process.returncode:
        if error_context:
            error_context = f" to get {error_context}"
        else:
            error_context = ""
        logging.error(f"Failed to run '{' '.join(command)}'{error_context}")
        logging.error(err.decode())
        return None
    return out.decode()


class ComputedValueProcessor:
    FUNCTIONS = (local_branch_name, remote_branch_name, branch_name)

    def __init__(self, data: dict):
        type_ = data.get("type", None)
        if not type_:
            sys.exit(f"Missing `type` for computed value: {dict(**data)}")
        function: typing.Optional[typing.Callable[[], Optional[str]]] = next(
            (function for function in self.FUNCTIONS if function.__name__ == type_),
            None,
        )
        if not function:
            available_types = [function.__name__ for function in self.FUNCTIONS]
            sys.exit(
                f"Unavailable type: '{type_}'. "
                f"Available types: {' '.join(available_types)}"
            )
        self.function: typing.Callable[[], Optional[str]] = function
        self.name = data.get("name", None) or type_
        self.regex = data.get("regex", None)
        self.default = data.get("default", None)
        self._data = data

    def get_data(self) -> typing.Dict[str, typing.Any]:
        value = self.function()
        if self.regex:
            match = re.search(self.regex, value) if value is not None else None
            if match:
                value = match.group("value")
            else:
                logging.warning(f"The regex '{self.regex}' didn't match '{value}'.")
                value = None
        if self.default and not value:
            value = self.default
        return {self.name: value}
