import base64
import os
import pathlib
import textwrap

import click
import tqdm

from github import Github
from github import InputGitTreeElement
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
import pyarrow.compute as pc
from openff.toolkit import Molecule


import click
import pathlib

REPO_NAME = "lilyminium/qca-datasets-report"

def draw_grid_df(
    df,
    use_svg: bool = True,
    output_file: str = None,
    n_col: int = 4,
    n_page: int = 24,
    subImgSize=(300, 300),
):
    """
    Draw molecules

    Parameters
    ----------
    df : pd.DataFrame
        The dataframe containing the molecules to draw.
    use_svg : bool, optional
        Whether to use SVG format, by default True
    output_file : str, optional
        The output file to save the images, by default None.
        If None, the images are not saved.
        If there are more than `n_page` images,
        the images are saved in chunks.
    n_col : int, optional
        The number of columns in the grid, by default 4
    n_page : int, optional
        The number of images per page, by default 24
    subImgSize : tuple, optional
        The size of the subimages, by default (300, 300)
    """
    from rdkit.Chem import Draw
    from openff.toolkit import Molecule
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF, renderPM
    import tempfile
    import os

    filenames = []
    
    rdmols = []
    legends = []
    n_confs = []
    unique_smiles = df["smiles"].unique()
    for smiles in unique_smiles:
        mol = Molecule.from_smiles(smiles, allow_undefined_stereo=True)
        rdmol = mol.to_rdkit()
        rdmols.append(rdmol)

        subdf = df[df["smiles"] == smiles]
        n_conf = len(subdf)
        legend = f"{n_conf} conformers"
        legends.append(legend)
        n_confs.append(n_conf)

    # sort by number of conformers
    indices = np.argsort(n_confs)[::-1]
    rdmols = [rdmols[i] for i in indices]
    legends = [legends[i] for i in indices]

    images = []
    for i in range(0, len(rdmols), n_page):
        j = i + n_page
        rdmols_chunk = rdmols[i:j]
        
        img = Draw.MolsToGridImage(
            rdmols_chunk,
            molsPerRow=n_col,
            subImgSize=subImgSize,
            # maxMols=n_page,
            returnPNG=False,
            useSVG=use_svg,
        )
        
        images.append(img)
    if output_file:
        output_file = pathlib.Path(output_file)
        output_file.parent.mkdir(exist_ok=True, parents=True)
        if not use_svg:
            images[0].save(output_file, append_images=images[1:], save_all=True, dpi=(300, 300))
            print(f"Saved {output_file}")
        else:
            base_file, suffix = str(output_file).rsplit(".", maxsplit=1)
            for i, img in enumerate(images):
                file = f"{base_file}_{i}.{suffix}"

                with tempfile.TemporaryDirectory() as tempdir:
                    cwd = os.getcwd()
                    os.chdir(tempdir)

                    try:
                        data = img.data
                    except AttributeError:
                        data = img
                    with open("temp.svg", "w") as f:
                        f.write(data)
                    drawing = svg2rlg("temp.svg")
                os.chdir(cwd)
                renderPM.drawToFile(drawing, file, fmt="PNG")
                print(f"Saved {file}")
                filenames.append(file)
    return filenames
    # return images


@click.command()
@click.option(
    "--pattern",
    type=str,
)
@click.option(
    "--output-directory",
    type=click.Path(exists=False, dir_okay=True, file_okay=False)
)
@click.option(
    "--issue-number",
    type=int,
)
@click.option(
    "--spec",
    "specs",
    required=False,
    type=str,
    multiple=True,
    default=[],
)
@click.option(
    "--dataset",
    "datasets",
    required=False,
    type=str,
    multiple=True,
    default=[],
)
@click.option(
    "--workflow-run-id",
    type=str,
)
def main(
    pattern: str,
    output_directory: str,
    issue_number: int,
    workflow_run_id: str,
    specs: list[str] = None,
    datasets: list[str] = None,
):
    g = Github(os.environ['GITHUB_TOKEN'])
    repo = g.get_repo(REPO_NAME)

    dataset = ds.dataset("tables")
    print(f"Loaded {dataset.count_rows()} molecules")

    if specs:
        expression = pc.field("specification").isin(specs)
        dataset = dataset.filter(expression)
        print(f"Filtered for specifications to {dataset.count_rows()} molecules")

    if datasets:
        expression = pc.field("dataset").isin(datasets)
        dataset = dataset.filter(expression)
        print(f"Filtered for datasets to {dataset.count_rows()} molecules")

    all_smiles = dataset.to_table(
        columns=["smiles"]
    ).to_pydict()["smiles"]
    unique_smiles = list(set(all_smiles))

    matching_smiles = []
    for smiles in tqdm.tqdm(
        unique_smiles,
        desc="Searching SMILES",
    ):
        mol = Molecule.from_smiles(smiles, allow_undefined_stereo=True)
        if mol.chemical_environment_matches(pattern):
            matching_smiles.append(smiles)

    cmd = f"search --pattern '{pattern}'"
    if specs:
        for spec in specs:
            cmd += f" --spec '{spec}'"
    if datasets:
        for dataset_name in datasets:
            cmd += f" --dataset '{dataset_name}'"

    commit_sha = ""
    embedded_files = []

    comment = textwrap.dedent(
        f"""
        # SMILES matches
        ## Query:
        ```
        {cmd}
        ```
        """)

    if not matching_smiles:
        comment += textwrap.dedent(
            f"""
            No matches found
            """
        )
    else:
        expression = pc.field("smiles").isin(matching_smiles)
        df = dataset.filter(expression).to_table().to_pandas()
        
        output_directory = pathlib.Path(output_directory)
        output_directory.mkdir(exist_ok=True, parents=True)
        csv = output_directory / "matching_molecules.csv"
        df.to_csv(csv, index=False)
        print(f"Saved {len(df)} matching molecules to {csv}")

        # draw as PNGs
        if len(df.smiles.unique()) < 100:
            molecule_directory = output_directory / "molecules"
            molecule_directory.mkdir(exist_ok=True, parents=True)
            filenames = draw_grid_df(df, output_file=molecule_directory / "molecules.png")

            # use pygithub to push molecules to images directory of assets branch
            remote_directory = f"{workflow_run_id}/molecules"
            element_list = []
            old_to_new = {}
            for filename in filenames:
                with open(filename, "rb") as image_file:
                    image_content = base64.b64encode(image_file.read()).decode("utf-8")
                blob = repo.create_git_blob(image_content, "utf-8")
                name = pathlib.Path(filename).name
                new_filename = f"{remote_directory}/{name}"
                old_to_new[filename] = new_filename
                element = InputGitTreeElement(
                    new_filename,
                    "100644",
                    "blob",
                    # image_content,
                    blob.sha,
                )
                element_list.append(element)
                embedded_files.append(new_filename)
            
            ref = repo.get_git_ref("heads/assets")
            latest_commit = repo.get_git_commit(ref.object.sha)
            base_tree = repo.get_git_tree(latest_commit.tree.sha)
            tree = repo.create_git_tree(element_list, base_tree)

            commit = repo.create_git_commit(
                f"Add matching molecules {workflow_run_id}",
                tree,
                [latest_commit],
            )
            ref.edit(commit.sha)
            commit_sha = commit.sha

            # edit contents after the fact
            for old, new in old_to_new.items():
                with open(old, "rb") as f:
                    image_content = f.read()
                repo_file = repo.get_contents(new, ref="assets")
                commit = repo.update_file(
                    new,
                    f"Add matching molecule {workflow_run_id}",
                    image_content,
                    repo_file.sha,
                    branch="assets",
                )


        else:
            print("Too many molecules to draw")


        comment += textwrap.dedent(
            f"""
            Unique matches: {len(matching_smiles)}
            Matching conformers: {len(df)}
            From datasets: {", ".join(df["dataset"].unique())}
            """
        )

        if commit_sha:
            molecule_file_texts = []
            for file in embedded_files:
                molecule_file_texts.append(f"![{file}](../blob/assets/{file}?raw=true)")
                # molecule_file_texts.append(f"![{file}](../blob/{commit_sha}/{file}?raw=true)")
            comment += "\n\n## Molecules\n\n<details>\n\n<summary>Click to expand for molecules</summary>\n\n"
            comment += "\n\n".join(molecule_file_texts)
            comment += "\n\n</details>"

        artifact_link = f"https://github.com/{REPO_NAME}/actions/runs/{workflow_run_id}"
        comment += "\n\n## Artifacts\n\n"
        comment += f"See the artifacts at the [GitHub Actions run]({artifact_link})."
        

    pr = repo.get_issue(issue_number)
    pr.create_comment(comment)


if __name__ == "__main__":
    main()

