import logging
import re
import subprocess
import sys
from typing import Optional, List


def remote_branch_name() -> Optional[str]:
    """Extract remote branch name"""
    return _value_from_process(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"]
    )


def local_branch_name() -> Optional[str]:
    """Extract local branch name"""
    return _value_from_process(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def branch_name() -> Optional[str]:
    """Extract local AND remote branch name separated by space"""
    data = []
    local = local_branch_name()
    if local:
        data.append(local)
    remote = remote_branch_name()
    if remote:
        data.append(remote)
    return " ".join(data)


def _value_from_process(command: List[str]) -> Optional[str]:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    if process.returncode:
        logging.error(f"Failed to run '{' '.join(command)}'")
        logging.error(err.decode())
        return None
    return out.decode()


class ComputedValueProcessor:
    FUNCTIONS = (local_branch_name, remote_branch_name, branch_name)

    def __init__(self, data: dict):
        type_ = data.pop("type", None)
        if not type_:
            sys.exit(f"Missing `type` for computed value: {data}")
        self.function = next(
            (function for function in self.FUNCTIONS if function.__name__ == type_),
            None,
        )
        if not self.function:
            available_types = [function.__name__ for function in self.FUNCTIONS]
            sys.exit(
                f"Unavailable type: '{type_}'. "
                f"Available types: {' '.join(available_types)}"
            )
        self.name = data.pop("name", None) or type_
        self.regex = data.pop("regex", None)
        self.default = data.pop("default", None)

    def get_data(self):
        value = self.function()
        if self.regex:
            match = re.search(self.regex, value)
            if match:
                value = match.group("value")
        return {self.name: value}
