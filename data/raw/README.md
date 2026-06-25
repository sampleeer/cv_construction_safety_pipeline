# Raw CelebA data

Place the official CelebA attributes annotation file here:

```text
data/raw/list_attr_celeba.txt
```

The dataset page is:

```text
http://mmlab.ie.cuhk.edu.hk/projects/CelebA.html
```

The project can run in demo mode when the raw file is absent. For the final lab run,
download the official annotations, place the file in this directory, then run:

```bash
dvc add data/raw/list_attr_celeba.txt
dvc repro
```
