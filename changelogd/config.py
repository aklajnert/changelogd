import logging

import click


class Config:
    @classmethod
    def set_verbosity(
        cls, ctx: click.core.Context, option: click.core.Option, verbose: int
    ) -> None:
        levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
        logging.basicConfig(
            level=levels.get(verbose, logging.WARNING),
            format="%(asctime)s - %(message)s",
        )
