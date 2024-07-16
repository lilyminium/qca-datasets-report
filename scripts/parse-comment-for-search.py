import click
import re

SMILES_PATTERN = re.compile("-pattern\s+[\'\"]*([0-9a-zA-Z\,\+\(\)\$\:\!\&\-\=\#\~\[\]]+)[\'\"]*", re.IGNORECASE)
MAX_MOLS_PATTERN = re.compile("-max-mols\s+([0-9]+)", re.IGNORECASE)


REGEXES = {
    "dataset": re.compile("-dataset\s+[\'\"]*([\w\-\s]+)[\'\"]*"),
    "spec": re.compile("-spec\s+[\'\"]*([\w\-]+)[\'\"]*"),
    "type": re.compile("-type\s+[\'\"]*([\w]+)[\'\"]*"),
    "combination": re.compile("-combination\s+[\'\"]*([\w\-\.]+)[\'\"]*"),
}

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

    for key, pattern in REGEXES.items():
        matches = pattern.findall(text)
        for match in matches:
            command += f" --{key} '{match}'"

    max_mols_matches = MAX_MOLS_PATTERN.findall(text)
    if len(max_mols_matches) > 1:
        raise ValueError(f"Pattern {text} contains multiple max-mols.")
    
    for match in max_mols_matches:
        command += f" --max-mols {match}"

    print(command)

if __name__ == "__main__":
    main()
