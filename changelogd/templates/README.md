# Introduction

Working with changelogs in this project requires the 
[changelogd](https://github.com/aklajnert/changelogd) installed. To install it, 
run the following command (requires Python 3.4 or newer):

```shell
pip install --upgrade changelogd
```

# Creating a new changelogd entry

To create a new entry, use `changelogd entry` command. After replying to a few 
questions, the entry file will be created in the `changelog.d` directory.

# Releasing a new version

A new version can be released by running `changelogd release <version>` where 
`<version>` is the new version's name, e.g. `1.1.3`. This command will remove 
all entry files, and create a new one with the release representation.

# Partial releases

Partial release is for a work-in-progress versions, that might not be released
yet. The partial release doesn't remove entry files nor create a new release. 
To execute partial release run `changelogd partial`, which will regenerate the 
output changelog file.
