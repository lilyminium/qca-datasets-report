import click

import pathlib
import pandas as pd


@click.command()
@click.option(
    "--targets-path",
    required=True,
    type=str,
    help="Path to the directory containing the targets.",
)
@click.option(
    "--output-path",
    required=True,
    type=str,
    help="Path to the output csv file.",
)
def main(
    targets_path: str,
    output_path: str,
):
    targets_path = pathlib.Path(targets_path)

    all_entries = []

    torsiondrives = targets_path.glob("torsion-*")
    for torsiondrive in torsiondrives:
        td_id = int(torsiondrive.stem.split("-")[-1])
        entry = {
            "type": "torsiondrive",
            "id": td_id,
        }
        all_entries.append(entry)
    
    optimizations = targets_path.glob("opt-*/*.xyz")
    for optimization in optimizations:
        opt_id = int(optimization.stem.split("-")[0])
        entry = {
            "type": "optimization",
            "id": opt_id,
        }
        all_entries.append(entry)
    
    df = pd.DataFrame(all_entries)
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
