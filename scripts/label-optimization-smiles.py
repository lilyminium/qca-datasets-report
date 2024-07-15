import json
import pathlib

import click
import tqdm

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from openff.toolkit import Molecule

def canonicalize_smiles(smi: str) -> str:
    mol = Molecule.from_smiles(smi, allow_undefined_stereo=True)
    return mol.to_smiles(isomeric=True, explicit_hydrogens=False)


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
    # parse optimizations

    with open(input_file, "r") as f:
        data = json.load(f)

    entries = data["entries"]["https://api.qcarchive.molssi.org:443/"]
    
    df = pd.DataFrame(entries)
    df = df.rename(columns={"record_id": "qcarchive_id"})

    MAPPED_SMILES_TO_SMILES = {
        smi: canonicalize_smiles(smi)
        for smi in tqdm.tqdm(
            df.cmiles.unique(),
            desc="Canonicalizing SMILES",
        )
    }

    dataset = pathlib.Path(input_file).stem
    spec = pathlib.Path(input_file).parent.name
    df["smiles"] = [
        MAPPED_SMILES_TO_SMILES[smi]
        for smi in df.cmiles.values
    ]
    df["dataset"] = dataset
    df["specification"] = spec
    df["torsiondrive_id"] = -1
    df["dihedral_indices"] = [[-1, -1, -1, -1] for _ in range(len(df))]
    df["grid_ids"] = [[-1] for _ in range(len(df))]
    table = pa.Table.from_pandas(df)
    
    output_directory = pathlib.Path(output_directory)
    output_file = output_directory / spec / f"{dataset}.parquet"
    output_file.parent.mkdir(exist_ok=True, parents=True)
    pq.write_table(table, output_file)


if __name__ == "__main__":
    main()
