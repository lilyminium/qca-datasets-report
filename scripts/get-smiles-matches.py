import base64
import os
import pathlib
import requests

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



def get_dataset_and_command_suffix(
    specs: list[str] = None,
    datasets: list[str] = None,
    types: list[str] = None,
    combinations: list[str] = None,
    dataset_directory: str = "tables",
    combinations_directory: str = "combinations"
) -> tuple[ds.FileSystemDataset, str]:
    dataset = ds.dataset(dataset_directory)
    print(f"Loaded {dataset.count_rows()} molecules")

    command_suffix = ""

    if combinations:
        combination_dfs = []
        for combination in combinations:
            df_file = pathlib.Path(combinations_directory) / f"{combination}.csv"
            combination_df = pd.read_csv(df_file)
            combination_dfs.append(combination_df)
        combination_df = pd.concat(combination_dfs)
        optimizations = combination_df[combination_df["type"] == "optimization"].id.values
        torsiondrives = combination_df[combination_df["type"] == "torsiondrive"].id.values

        expression = (
            pc.field("qcarchive_id").isin(optimizations)
            | pc.field("qcarchive_id").isin(torsiondrives)
        )
        dataset = dataset.filter(expression)
        print(f"Filtered for combinations to {dataset.count_rows()} molecules")

        for combination in combinations:
            command_suffix += f" --combination '{combination}'"


    if specs:
        expression = pc.field("specification").isin(specs)
        dataset = dataset.filter(expression)
        print(f"Filtered for specifications to {dataset.count_rows()} molecules")

        for spec in specs:
            command_suffix += f" --spec '{spec}'"

    if datasets:
        expression = pc.field("dataset").isin(datasets)
        dataset = dataset.filter(expression)
        print(f"Filtered for datasets to {dataset.count_rows()} molecules")

        for dataset_name in datasets:
            command_suffix += f" --dataset '{dataset_name}'"

    if types:
        expression = pc.field("type").isin(types)
        dataset = dataset.filter(expression)
        print(f"Filtered for types to {dataset.count_rows()} molecules")

        for type_name in types:
            command_suffix += f" --type '{type_name}'"
    
    return dataset, command_suffix



def post_discussion_comment(
    repo,
    discussion_id: str,
    comment: str,
):
    # REST API not yet supported
    # must use graphql to add discussion comment

    query = f"""
    mutation {{
        addDiscussionComment(input: {{
            discussionId: "{discussion_id}",
            body: "{comment}"
        }}) {{
            comment {{
                id
            }}
        }}
    }}
    """
    token = os.environ['GITHUB_TOKEN']
    headers = {
        "Authorization": "token " + token,
    }
    response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json={"query": query},
    )
    response.raise_for_status()


    # repo._requester.requestJsonAndCheck(
    #     "POST",
    #     f"{repo.url}/discussions/{discussion_number}/comments",
    #     input={
    #         "body": comment,
    #     }
    # )


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
    "--discussion-id",
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
    "--type",
    "types",
    required=False,
    type=str,
    multiple=True,
    default=[],
)
@click.option(
    "--combination",
    "combinations",
    required=False,
    type=str,
    multiple=True,
    default=[],
)
@click.option(
    "--combinations-directory",
    type=click.Path(exists=True, dir_okay=True, file_okay=False)
)
@click.option(
    "--workflow-run-id",
    type=str,
)
def main(
    pattern: str,
    output_directory: str,
    discussion_id: int,
    workflow_run_id: str,
    specs: list[str] = None,
    datasets: list[str] = None,
    types: list[str] = None,
    combinations: list[str] = None,
    combinations_directory: str = "combinations"
):
    g = Github(os.environ['GITHUB_TOKEN'])
    repo = g.get_repo(REPO_NAME)
    
    dataset, command_suffix = get_dataset_and_command_suffix(
        specs=specs,
        datasets=datasets,
        types=types,
        combinations=combinations,
        combinations_directory=combinations_directory
    )
    

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

    cmd = f"botsearch --pattern '{pattern}'" + command_suffix



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

        counts = df.groupby(by=["type", "dataset", "specification"]).count().reset_index()
        counts = counts[["type", "dataset", "specification", "smiles"]]
        counts = counts.rename(columns={"smiles": "# conformers"})
        counts = counts.sort_values(by=["type", "dataset", "specification"])

        comment += textwrap.dedent(
            f"""
            Unique matches: {len(matching_smiles)}
            Matching conformers: {len(df)}
            Number of datasets: {len(df.dataset.unique())}

            ## Counts

            <details>

            <summary>Click to expand for counts</summary>

            """
        ) + counts.to_markdown(index=False) + "\n\n</details>"

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
        comment += f"See the artifacts at the [GitHub Actions run]({artifact_link}). They will expire in 7 days."
    
    post_discussion_comment(repo, discussion_id=discussion_id, comment=comment)


if __name__ == "__main__":
    main()

