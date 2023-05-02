import pathlib
from typing import Dict
from pathlib import Path

import yaml
import re
import os
import subprocess


def open_yaml_file(file_path: str) -> dict:
    with open(file_path, "r") as stream:
        return yaml.safe_load(stream)


def get_containers_and_version(file_path: str) -> Dict[str, str]:
    """
    returns name and version of docker-compose.yml as a dict
    :param file_path: file path to yaml file
    :return: dict
    """
    yaml_content = open_yaml_file(file_path)
    services = yaml_content["services"]

    containers = {}
    for service_definition in services.values():
        name_and_version = re.search(
            "([\w]*-[\w]*){1,}:[\d]*\.[\d]*\.[\d]*", service_definition["image"]
        )
        container_name, container_version = re.split(":", name_and_version.group())
        containers[container_name] = container_version

    return containers


def generate_license_file() -> None:
    """
    generates file with licenses
    :param
    :return:
    """
    containers = get_containers_and_version(
        "/home/azubi/PycharmProjects/edge-license-listing/yml_files/docker-compose.yml")

    for container, version in containers.items():
        git_clone_repo(container)
        git_checkout_tag(container, version)
        pyproject_toml_path = Path("/home/azubi/PycharmProjects/edge-license-listing/"+container+"/pyproject.toml")
        if pyproject_toml_path.is_file():
            create_venv(container, "/home/azubi/PycharmProjects/edge-license-listing/"+container)

    cmd = "pip-licenses --format=rst --output-file=/tmp/output.rst"
    os.system(cmd)


def git_clone_repo(repo_name):
    ssh = "git@github.com:kraussmaffei/" + repo_name + ".git"
    return subprocess.check_call(['git'] + ['clone'] + [ssh])


def git_checkout_tag(container, version):
    tag = "v" + version
    compl = subprocess.run("git checkout " + tag, shell=True, cwd=str(pathlib.Path.cwd() / container))


def create_venv(repo_name, path):
    subprocess.check_call(['virtualenv'] + [path+repo_name])
