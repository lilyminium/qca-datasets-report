# qca-datasets-report

**Note: this repo is under development and support is not guaranteed.**

This repo lets you search the corpus of
[qca-dataset-submission](https://github.com/openforcefield/qca-dataset-submission)
for existing data.

To search: in an issue, make a comment

```
botsearch --smiles '[#15:1]-[#16:2]'
```

Optionally, limit the specifications searched (note: only the 'default' specification has been download for now.)

```
botsearch --smiles '[#15:1]-[#16:2]' --spec 'default'
```

Optionally, limit the datasets searched (multiple dataset supported).

```
botsearch --smiles '[#15:1]-[#16:2]' --dataset 'SMIRNOFF Coverage Set 1' --dataset 'OpenFF Optimization Set 1'
```

Optionally, limit the dataset type searched.

```
botsearch --smiles '[#15:1]-[#16:2]' --type 'optimization'
botsearch --smiles '[#15:1]-[#16:2]' --type 'torsiondrive'
```

Optionally, limit to just a subset of data, e.g. the Sage 2.2.0 training set. This uses combinations of QCA IDs put together in the `combinations/` directory.

```
botsearch --smiles '[#15:1]-[#16:2]' --combination 'sage-2.2.0'
```

A GitHub Action will get started searching for the molecule.
The record IDs will get saved as an artifact.