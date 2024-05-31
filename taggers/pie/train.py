import os
import sys
import shutil

if __name__ == "__main__":
    # Console args
    train_set_path = sys.argv[1]
    dev_set_path = sys.argv[2]
    config_path = sys.argv[3]
    docker_path = sys.argv[4]
    # Set pie env
    os.environ["PIE_MODELNAME"] = docker_path.split("/")[-1]
    os.environ["PIE_MODELPATH"] = docker_path
    os.environ["PIE_INPUT_PATH"] = train_set_path
    os.environ["PIE_DEV_PATH"] = dev_set_path
    os.environ["PIE_DEVICE"] = "cuda:0"
    # Run tagger
    this_dir = os.path.dirname(os.path.realpath(__file__))
    os.system(f"python3 {this_dir}/pie/train.py {config_path}")
