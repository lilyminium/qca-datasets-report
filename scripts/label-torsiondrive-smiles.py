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
    from openff.qcsubmit.results import TorsionDriveResultCollection

    dataset_name = pathlib.Path(input_file).stem
    spec = pathlib.Path(input_file).parent.name
    dataset = TorsionDriveResultCollection.parse_file(input_file)

    td_record_to_cmiles_and_inchi = {
        entry.record_id: (entry.cmiles, entry.inchi_key)
        for entry in dataset.entries['https://api.qcarchive.molssi.org:443/']
    }

    unique_cmiles = set(cmiles for cmiles, _ in td_record_to_cmiles_and_inchi.values())
    cmiles_to_smiles = {
        cmiles: canonicalize_smiles(cmiles)
        for cmiles in tqdm.tqdm(unique_cmiles, desc="Canonicalizing SMILES")
    }

    records_and_molecules = dataset.to_records()
    all_entries = []
    for record, openff_molecule in tqdm.tqdm(records_and_molecules):
        cmiles, inchi_key = td_record_to_cmiles_and_inchi[record.id]

        dihedrals = [
            list(dih)
            for dih in record.specification.keywords.dihedrals
        ]

        for grid_id, optimization in record.minimum_optimizations.items():
            entry = {
                "type": "torsiondrive",
                "qcarchive_id": optimization.id,
                "cmiles": cmiles,
                "inchi_key": inchi_key,
                "smiles": cmiles_to_smiles[cmiles],
                "dataset": dataset_name,
                "specification": spec,
                "torsiondrive_id": record.id,
                "dihedral_indices": dihedrals,
                "grid_id": list(grid_id),
            }
            all_entries.append(entry)

    table = pa.Table.from_pylist(all_entries)
    output_directory = pathlib.Path(output_directory)
    output_file = output_directory / spec / f"{dataset_name}.parquet"
    output_file.parent.mkdir(exist_ok=True, parents=True)
    pq.write_table(table, output_file)


if __name__ == "__main__":
    main()
