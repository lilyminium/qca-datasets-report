import click
import re

SMILES_PATTERN = re.compile("-pattern\s+[\'\"]*([0-9a-zA-Z,+()$:-=#~\[\]]+)[\'\"]*", re.IGNORECASE)
DATASET_PATTERN = re.compile("-dataset\s+[\'\"]*([\w-]+)[\'\"]*")
SPEC_PATTERN = re.compile("-spec\s+[\'\"]*([\w-]+)[\'\"]*")
TYPE_PATTERN = re.compile("-type\s+[\'\"]*([\w]+)[\'\"]*")
COMBINATION_PATTERN = re.compile("-combination\s+[\'\"]*([\w]+)[\'\"]*")

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

    smiles = matches[0]

    command = (
        "python scripts/get-smiles-matches.py "
        f"--pattern '{smiles}'"
    )

    dataset_matches = DATASET_PATTERN.findall(text)
    for match in dataset_matches:
        command += f" --dataset '{match}'"
    
    spec_matches = SPEC_PATTERN.findall(text)
    for match in spec_matches:
        command += f" --spec '{match}'"
    
    type_matches = TYPE_PATTERN.findall(text)
    for match in type_matches:
        command += f" --type '{match}'"
    
    combination_matches = COMBINATION_PATTERN.findall(text)
    for match in combination_matches:
        command += f" --combination '{match}'"

    print(command)

if __name__ == "__main__":
    main()
