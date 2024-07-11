import click
import tqdm

from qcportal import PortalClient
import pandas as pd


@click.command()
@click.option(
    "--output-file",
    type=click.Path(exists=False, dir_okay=False, file_okay=True)
)
def main(
    output_file: str,
):
    client = PortalClient("https://api.qcarchive.molssi.org:443")
    datasets = client.list_datasets()
    # get specifications
    for entry in tqdm.tqdm(datasets):
        dataset = client.get_dataset(entry["dataset_type"], entry["dataset_name"])
        specifications = dataset.specifications
        entry["specifications"] = sorted(specifications)

    df = pd.DataFrame(datasets)
    df.to_csv(output_file, index=False)
    print(f"Saved {len(df)} datasets to {output_file}")


if __name__ == "__main__":
    main()
