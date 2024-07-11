import click
import re

SMILES_PATTERN = re.compile("smiles: ([0-9a-zA-Z\+\#\[\]\:\!\~\-\=\(\)\$\*]+)", re.IGNORECASE)

@click.command()
@click.option(
    "--text",
    type=str,
)
def main(
    text: str,
):
    matches = SMILES_PATTERN.findall(text)
    if len(matches) == 0:
        raise ValueError(f"Pattern {text} does not contain any SMILES.")

    if len(matches) > 1:
        raise ValueError(f"Pattern {text} contains multiple SMILES.")

    print(matches[0])

if __name__ == "__main__":
    main()
