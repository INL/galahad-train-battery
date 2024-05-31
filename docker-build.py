# Standard library
import os
import sys

# Local
from constants import VERSION, DOCKER, DOCKER_TAG_PREFIX


def build_single_folder(folder_name: str) -> None:
    """
    Build a single docker image from a folder.
    """
    tagger_name = folder_name.split("/")[0]
    config_name = folder_name.split("/")[-1]
    print(
        f"docker build -t {DOCKER_TAG_PREFIX}{tagger_name}-{config_name}:{VERSION} {DOCKER}/{folder_name}"
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Build specified trained model from DOCKER/
        configs = sys.argv[1:]
        for config in configs:
            build_single_folder(config)
    else:
        # Retrieve all trained models from DOCKER/
        all_configs = []
        _, tagger_dirs, _ = next(os.walk(DOCKER))
        for tagger_dir in tagger_dirs:
            _, config_dirs, _ = next(os.walk(f"{DOCKER}/{tagger_dir}"))
            all_configs.extend(
                [f"{tagger_dir}/{config_dir}" for config_dir in config_dirs]
            )
        # Build them all
        for config in all_configs:
            build_single_folder(config)
