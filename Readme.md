# galahad-train-battery (0.9.0)
Python program for training linguistic annotation taggers based on a configuration file and list of datasets. It prepares the resulting trained models for dockerization and adds relevant metadata. It is tagger software agnostic as long as a simple Python shell is built around it.

### GaLAHaD-related Repositories
- [galahad](https://github.com/INL/galahad)
- [galahad-train-battery](https://github.com/INL/galahad-train-battery) [you are here]
- [galahad-taggers-dockerized](https://github.com/INL/galahad-taggers-dockerized) [to be released]
- [galahad-corpus-data](https://github.com/INL/galahad-corpus-data/)
- [int-pie](https://github.com/INL/int-pie)
- [int-huggingface-tagger](https://github.com/INL/huggingface-tagger) [to be released]

# Setup
1. `git clone --recurse-submodules https://github.com/INL/galahad-train-battery`
2. Run `unzip-and-clean-corpus.sh`
3. Run `train.py` (see usage below).

# How to use
Running `python3 train.py` trains all configs found in `configs/`. To train a specific config, supply its directory name relative to `configs/`. E.g. `python3 train.py pie/tdn`, or supply multiple. Once trained, the models will appear in the `galahad-taggers-dockerized/` folder. `docker-build.py` builds all models to images. Optionally, supply one or more specific configurations as an argument: `python3 docker-build.py pie/tdn`.

## Configurations
The first level of folders in `configs/` dictates what tagger is used. A tagger with *the same* directory name must exist in `taggers/`. The second level of folders correspond to models: each configuration will train a single model. A config folder contains a `datasets.json` and `config.json` file. The format of `datasets.json` is:

```json
{
  "datasets": ["my-first-dataset", "my-second-dataset"]
}
```

Dataset names (e.g. `my-first-dataset`) must correspond to a folder in `galahad-corpus-data/training-data` (e.g. `galahad-corpus-data/training-data/my-first-dataset/`). When multiple datasets are specified, they will be merged automatically. The format of `config.json` is up to the specific tagger and can be used to set parameters such as learning rate.

## Datasets
Each folder in `galahad-corpus-data/training-data` contains one dataset, pre-split in train, dev and test. A dataset must have three files that end in `*train.tsv`, `*dev.tsv` and `*test.tsv` respectively. If multiple matching files exist, the first is chosen. 
To support the merging of datasets, tsv files **cannot** have headers. That does mean that only datasets with the same column order should be merged, so pay attention to this when selecting datasets to merge. 
Tsv files are expected to have the same number of tabs (`\t`) on each line. This is especially important for taggers that read the first line to determine the number of columns.

See the [galahad-corpus-data repository](https://github.com/INL/galahad-corpus-data/) for more information on the datasets.

## Docker
Training a configuration creates a folder in `galahad-taggers-dockerized/[tagger-name]/[config-name]` where the trained model is stored. It uses a docker prefab as a base to create this folder, stored in `docker-prefabs/[tagger-name]/`. I.e., any files in the prefab (such as a Dockerfile) are conveniently copied over.

See https://github.com/INL/galahad-taggers-dockerized/ for more information on how to hook up a trained model to Galahad.

# How it works: the training process
When you run `train.py`, it:
1. merges datasets defined in `datasets.json` (if multiple are defined) and stores them in `galahad-corpus-data/training-data/[dataset1]-[dataset2]/`
2. creates an output folder at `galahad-taggers-dockerized/[tagger-name]/[config-name]`.
3. copies over `config.json` and `datasets.json` to the output folder for sake of provenance.
4. copies over the contents of `docker-prefabs/[tagger-name]` to the output folder (overwriting the json files if desired).
5. creates a virtual environment for the tagger located at `taggers/[tagger-name]/venv/`.
6. runs `taggers/[tagger-name]/[tagger-name]/requirements.sh` that installs all necessary packages in the venv.
7. calls `taggers/[tagger-name]/train.py` from the venv with 4 console arguments (see below).
8. Lastly, the tagger and its own `train.py` are now expected to produce a model at `galahad-taggers-dockerized/[tagger-name]`.

## Why .sh instead of pip -r requirements.txt?
Use of `--no-deps` is not yet supported for requirements.txt (see https://github.com/pypa/pip/pull/10837). Some taggers need to install packages with `--no-deps`. This is a workaround.
If you don't need this, your `requirements.sh` can be as simple as:
```sh
pip install -r requirements.txt
```

# How to add a new tagger for training
1. To add a new tagger, create the folder `taggers/my-tagger`.
2. In here, create `train.py`. This file will be called by the `train.py` at the repo root. It will provide 4 console arguments: `python3 taggers/my-tagger/train.py [train_set_path] [dev_set_path] [config_path] [docker_path]`. `train_set_path` and `dev_set_path` will each refer to a single tsv file. `config_path` refers to a json file in `configs/my-tagger/some-configuration`. `docker_path` will refer to a folder where your tagger can save its trained model.
3. Add the code of your own tagger. Git clone your tagger to `taggers/my-tagger/my-tagger`. Configure your `train.py` so that it will train your tagger, and provide a `requirements.sh` in your cloned repository `taggers/[tagger-name]/[tagger-name]/requirements.sh`.
4. Add all the files that you want to be copied over to `docker_path` at `docker-prefabs/my-tagger`. A `Dockerfile` for example.
5. Add a configuration for your tagger at `configs/my-tagger/some-configuration`. This contains a `datasets.json` and a `config.json`. You can use the latter for specific configuration for your tagger.
6. Now, run `python3 train.py my-tagger/some-configuration`. The output model should appear in `galahad-taggers-dockerized/my-tagger`. You can now dockerize your tagger. See the [galahad-taggers-dockerized repository](https://github.com/INL/galahad-taggers-dockerized) for further steps with your docker container.

# Example folder structure
```python
galahad-train-battery/
- galahad-corpus-data/
  - training-data/
    - first/
      - *train.tsv
      - *dev.tsv
      - *test.tsv
    - second/
      - *train.tsv
      - *dev.tsv
      - *test.tsv
    - pie-first-second/ # created automatically by merging the datasets
- galahad-taggers-dockerized/
  - pie/
    - first-second/ # folder is created
      - Dockerfile # copied over from docker-prefabs
- taggers/
  - pie/ 
    - pie/
      - requirements.sh
    - train.py
- docker-prefabs/
  - pie/
    - Dockerfile
- configs/
  - pie/
    - first-second/
      - config.json
      - datasets.json # specifies both datasets
- train.py
- docker-build.py
```

# Dev info
- We use the [Black](https://black.readthedocs.io/en/stable/index.html) formatter.
- Python 3.10.12
