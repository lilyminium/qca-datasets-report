# qca-datasets-report

**Note: this repo is under development and support is not guaranteed.**

This repo lets you search the corpus of
[qca-dataset-submission](https://github.com/openforcefield/qca-dataset-submission)
for existing data.


## Searching
In a [GitHub discussion](https://github.com/lilyminium/qca-datasets-report/discussions/categories/search-qca),
make either a **new Discussion** or a comment in an existing discussion. If a new Discussion, it must be
labelled with `botsearch` to trigger the search.

The command *must* include a valid SMARTS `--pattern`.

```
botsearch --pattern '[#15:1]-[#16:2]'
```

Optionally, limit the specifications searched (note: only the 'default' specification has been download for now.)

```
botsearch --pattern '[#15:1]-[#16:2]' --spec 'default'
```

Optionally, limit the datasets searched (multiple dataset supported).

```
botsearch --pattern '[#15:1]-[#16:2]' --dataset 'SMIRNOFF Coverage Set 1' --dataset 'OpenFF Optimization Set 1'
```

Optionally, limit the dataset type searched.

```
botsearch --pattern '[#15:1]-[#16:2]' --type 'optimization'
botsearch --pattern '[#15:1]-[#16:2]' --type 'torsiondrive'
```

Optionally, limit to just a subset of data, e.g. the Sage 2.2.0 training set. This uses combinations of QCA IDs put together in the `combinations/` directory.

```
botsearch --pattern '[#15:1]-[#16:2]' --combination 'sage-2.2.0'
```

A GitHub Action will get started searching for the molecule.
The record IDs will get saved as an artifact.
If under a certain number of molecules are matched (up to 300), the molecules
will get rendered as images and returned.
