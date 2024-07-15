import pathlib
import typing

import click
import tqdm

@click.command()
@click.option(
    "--dataset",
    "datasets",
    multiple=True,
    type=str
)
@click.option(
    "--spec",
    "spec_name",
    type=str
)
@click.option(
    "--output-directory",
    type=click.Path(exists=False, dir_okay=True, file_okay=True)
)
@click.option(
    "--type",
    "dataset_type",
    type=click.Choice(["singlepoint", "optimization", "torsiondrive"])
)
def download(
    datasets: list[str],
    dataset_type: typing.Literal["singlepoint", "optimization", "torsiondrive"],
    spec_name: str = "default",
    output_directory: str = "input",
):
    from qcportal import PortalClient
    from openff.qcsubmit.results import (
        BasicResultCollection,
        OptimizationResultCollection,
        TorsionDriveResultCollection,
    )

    output_directory = pathlib.Path(output_directory)
    output_directory.mkdir(exist_ok=True, parents=True)

    CLASSES = {
        "singlepoint": BasicResultCollection,
        "optimization": OptimizationResultCollection,
        "torsiondrive": TorsionDriveResultCollection
    }

    klass = CLASSES[dataset_type.lower()]

    client = PortalClient("https://api.qcarchive.molssi.org:443")
    for dataset in tqdm.tqdm(datasets):
        ds = klass.from_server(
            client=client,
            datasets=[dataset],
            spec_name=spec_name,
        )
        stem = dataset + ".json"
        output = output_directory / dataset_type / spec_name / stem
        output.parent.mkdir(exist_ok=True, parents=True)
        with output.open("w") as f:
            f.write(ds.json(indent=2))
        print(f"Wrote to {output}")


if __name__ == "__main__":
    download()
