import pathlib
from pprint import pprint

import click

from wfd_scorer import twenty_twenty_four


@click.command()
@click.argument(
    "filename", type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path)
)
@click.argument("power", type=int)
def score_file(filename: pathlib.Path, power: int):
    print(f"Opening {filename=}")
    with filename.open() as fp:
        lines = fp.readlines()

    pprint(lines)

    parsed_lines = [twenty_twenty_four.parse_line(line.upper()) for line in lines]

    for line in lines:
        print(f"{line=}")
        print(f"{twenty_twenty_four.parse_line(line)}")

    score = twenty_twenty_four.score_lines(parsed_lines, power=power)

    print(f"Total score={score}")


def main():
    pass


if __name__ == "__main__":
    score_file()
