import json
import pathlib

import click


@click.command()
@click.option(
    "--input-directory",
    type=click.Path(exists=True, dir_okay=True, file_okay=False)
)
@click.option(
    "--output-directory",
    type=click.Path(exists=False, dir_okay=True, file_okay=False)
)
def main(
    input_directory: str,
    output_directory: str,
):
    input_directory = pathlib.Path(input_directory)
    json_files = list(input_directory.glob("*/*.json"))
    output_directory = pathlib.Path(output_directory)
    output_directory.mkdir(exist_ok=True, parents=True)
    parquet_files = list(output_directory.glob("*/*.parquet"))
    new_files = []

    for json_file in json_files:
        dataset = json_file.stem
        spec = json_file.parent.name
        parquet_file = output_directory / spec / f"{dataset}.parquet"
        if parquet_file not in parquet_files:
            new_files.append({
                "file": str(json_file)
            })
    
    print(json.dumps(new_files))
    

if __name__ == "__main__":
    main()