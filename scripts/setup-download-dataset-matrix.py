import ast
import json
import pathlib

import click
import pandas as pd


@click.command()
@click.option(
    "--input-file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True)
)
@click.option(
    "--output-directory",
    type=click.Path(exists=False, dir_okay=True, file_okay=False)
)
def main(
    input_file: str,
    output_directory: str,
):
    df = pd.read_csv(input_file)
    entries = []
    for _, row in df.iterrows():
        # only treat singlepoints, optimizations, torsiondrives
        allowed_datasets = [
            "singlepoint",
            "optimization",
            "torsiondrive",
        ]
        if row["dataset_type"] not in allowed_datasets:
            continue
        specifications = ast.literal_eval(row["specifications"])
        for spec in specifications:
            # check if file exists
            output_directory = pathlib.Path(output_directory)
            stem = row["dataset_name"].replace(" ", "-") + ".json"
            output_file = output_directory / row["dataset_type"] / spec / stem
            if output_file.exists():
                continue

            # temporarily only keep optimization/default
            if not row["dataset_type"] == "optimization" or not spec == "default":
                continue

            entry = {
                "dataset": row["dataset_name"],
                "type": row["dataset_type"],
                "spec": spec,
            }
            entries.append(entry)


    # only 256 entries allowed
    json_str = json.dumps(entries[:256])
    print(json_str)



if __name__ == "__main__":
    main()