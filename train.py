# Standard library
import json
import os
import shutil
import sys
import time

# local
from constants import CONFIGS, DATASETS, DOCKER, LOGS, PREFABS, TAGGERS


def train_single_folder(folder_name: str) -> None:
    """
    Run train.py for a single folder.
    folder_name: in the format [tagger_name]/[config_name]
    """
    tagger_name, config_name, config_path, dataset_config_path = get_folder_info(
        folder_name
    )
    print(f"Setting up tagger [{tagger_name}] with config [{config_name}].")
    # Get the dataset path from the json config file. Possibly merge multiple datasets to do so.
    merged_name = f"{tagger_name}-{config_name}"
    dataset_path = get_dataset_path(dataset_config_path, merged_name)
    dataset_name = dataset_path.split("/")[-1]
    docker_path = create_docker_from_prefab(folder_name)
    # Run tagger
    run_tagger(tagger_name, config_path, dataset_name, docker_path, config_name)


def get_folder_info(folder_name: str) -> tuple[str, str, str, str]:
    tagger_name = folder_name.split("/")[0]
    config_name = folder_name.split("/")[-1]
    config_path = f"{CONFIGS}/{folder_name}/config.json"
    dataset_config_path = f"{CONFIGS}/{folder_name}/datasets.json"
    return tagger_name, config_name, config_path, dataset_config_path


def get_dataset_path(dataset_config_path: str, merged_name: str) -> str:
    """
    Get dataset path, possibly by merging multiple datasets.
    dataset_config_path: in the format [tagger_name]/[config_name]/datasets.json
    Returns: path to the (possibly merged) dataset.
    """
    with open(dataset_config_path) as datasets_config_file:
        datasets: list[str] = json.load(datasets_config_file)["datasets"]
    dataset_path = f"{DATASETS}/{datasets[0]}"
    if len(datasets) > 1:
        dataset_path = merge_datasets(datasets, merged_name)
    return dataset_path


def merge_datasets(dataset_folders: list[str], merged_name: str) -> str:
    """
    Merge datasets to a single file
    dataset_folders: list of dataset names that exist in DATASETS/.
    Returns: path to the merged dataset.
    """
    dataset_names = [i.split("/")[-1] for i in dataset_folders]
    print(f"Merging datasets: {dataset_names}.")
    # Create path for merged dataset
    merged_path = f"{DATASETS}/{merged_name}"
    if not os.path.exists(merged_path):
        os.makedirs(merged_path)
    # Merge sets to new path
    for set_type in ["train", "dev", "test"]:
        dataset_paths: list[str | None] = [
            get_dataset_of_type(dataset_folder, set_type)
            for dataset_folder in dataset_folders
        ]
        # create new file for merged dataset
        with open(f"{merged_path}/{set_type}.tsv", "w+") as merged_dataset:
            for dataset_path in dataset_paths:
                # write each dataset to the merged dataset
                if dataset_path is None:
                    continue
                with open(dataset_path, "r") as dataset:
                    merged_dataset.write(dataset.read())
                    merged_dataset.write("\n\n")  # defines a new sentence
    # Return new path
    return merged_path


def get_dataset_of_type(dataset_name: str, type: str) -> str | None:
    """Get the path to a dataset of type train/test/dev."""
    folder_path = f"{DATASETS}/{dataset_name}"
    _, _, files = next(os.walk(folder_path))
    # next() gets the first of the filtered list.
    dataset_path = next((file for file in files if file.endswith(f"{type}.tsv")), None)
    if dataset_path is None:
        return None
    return f"{folder_path}/{dataset_path}"


def create_docker_from_prefab(folder_name: str) -> str:
    """
    Create a docker folder by copying everything from a prefab folder.
    Also copies over config.json and datasets.json from the CONFIG folder for sake of provenance.
    The prefab is copied last, so the json files can be overwritten if desired.
    """
    print("Creating docker output folder.")
    tagger_name, config_name, config_path, dataset_config_path = get_folder_info(
        folder_name
    )
    docker_path = f"{DOCKER}/{tagger_name}/{config_name}"
    # Create docker folder
    if not os.path.exists(docker_path):
        os.makedirs(docker_path)
    # Copy json
    shutil.copy(config_path, docker_path)
    shutil.copy(dataset_config_path, docker_path)
    # Update datasets.json with the provenance info from the datasets.json in the root folder
    add_dataset_provenance(docker_path)
    # Copy prefab folder
    if not os.path.exists(docker_path):
        shutil.copytree(f"{PREFABS}/{tagger_name}", docker_path)
    return docker_path


def add_dataset_provenance(docker_path: str) -> None:
    """
    Copy provenance from the root to the datasets.json file in the docker folder.
    """
    result = {"datasets": []}
    with open(f"{docker_path}/datasets.json", "r") as docker_file:
        datasets: list[str] = json.load(docker_file)["datasets"]

    corpora_folder = DATASETS.split("/")[0]
    with open(f"{corpora_folder}/datasets.json") as provenance_file:
        provenance: list = json.load(provenance_file)
        for dataset in datasets:
            # find object in list that matches trainingpath
            matching = [
                i for i in provenance if i["trainingPath"].split("/")[-1] == dataset
            ]
            if matching:
                result["datasets"].append(matching[0])
            else:
                result["datasets"].append({"name": dataset, "version": "unknown"})

    with open(f"{docker_path}/datasets.json", "w") as docker_file:
        json.dump(result, docker_file)


def run_tagger(
    tagger_name: str,
    config_path: str,
    dataset_name: str,
    docker_path: str,
    config_name: str,
) -> None:
    """
    Run the tagger with the given config and dataset and logs the output.
    """
    # Get train and dev set paths
    train_set_path = get_dataset_of_type(dataset_name, "train")
    dev_set_path = get_dataset_of_type(dataset_name, "dev")
    # Create venv
    venv_path = f"{TAGGERS}/{tagger_name}/venv"
    activate_venv = f". {venv_path}/bin/activate"
    tagger_dir = f"{TAGGERS}/{tagger_name}/{tagger_name}"
    if not os.path.exists(venv_path):
        print(
            f"No existing virtual environment was found for tagger [{tagger_name}]. Creating one."
        )
        os.system(f"python3 -m venv {venv_path}")
        os.system(f"{activate_venv} && cd {tagger_dir} && sh requirements.sh")
    # Create log folder
    if not os.path.exists(LOGS):
        os.makedirs(LOGS)
    # Run tagger
    print(
        f"Training tagger [{tagger_name}] with config [{config_name}]... (this will take a while)"
    )
    # Note the -u to ensure flushing
    start_train_py = f"python3 -u {TAGGERS}/{tagger_name}/train.py {train_set_path} {dev_set_path} {config_path} {docker_path}"
    start_time = int(time.time())
    log_path = f"{LOGS}/{config_name}-{start_time}.txt"
    os.system(f"{activate_venv} && {start_train_py} > {log_path} 2>&1")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specified configs
        configs = sys.argv[1:]
        for config in configs:
            train_single_folder(config)
    else:
        # Retrieve all from configs/
        all_configs = []
        _, tagger_dirs, _ = next(os.walk(CONFIGS))
        for tagger_dir in tagger_dirs:
            _, config_dirs, _ = next(os.walk(f"{CONFIGS}/{tagger_dir}"))
            all_configs.extend(
                [f"{tagger_dir}/{config_dir}" for config_dir in config_dirs]
            )
        # Run them all
        for config in all_configs:
            train_single_folder(config)
