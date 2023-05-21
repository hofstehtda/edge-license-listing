import json
import pathlib
import shutil
import argparse
from typing import Dict
from pathlib import Path

import yaml
import re
import subprocess

VENV_NAME = '_venv_licenses'


def open_yaml_file(file_path: str) -> dict:
    with open(file_path, "r") as stream:
        return yaml.safe_load(stream)


def get_containers_and_version(file_path: Path) -> Dict[str, str]:
    """
    returns name and version of docker-compose.yml as a dict
    :param file_path: file path to yaml file
    :return: dict
    """
    yaml_content = open_yaml_file(str(file_path))
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
    current_directory = Path(__file__).parent
    path_to_container = current_directory / "container"
    path_to_venv = "~/.pyenv/versions/"

    delete_directory(path_to_container)
    Path.mkdir(Path.cwd() / "container")

    clear_output_file(current_directory / "output.txt")
    clear_output_file(current_directory / "output0.txt")
    clear_output_file(current_directory / "output2.json")
    containers = get_containers_and_version(current_directory / "yml_files" / "docker-compose.yml")

    for container, version in containers.items():
        git_clone_repo(container)
        git_checkout_tag(container, version)
        pyproject_toml_path = Path(path_to_container / container / "pyproject.toml")
        if pyproject_toml_path.exists():
            python_version = get_python_version(pyproject_toml_path)
            create_venv(
                container,
                path_to_container / container,
                python_version,
                path_to_container,
            )
            create_license_file(path_to_container / container, container + VENV_NAME)
            delete_venv(container + VENV_NAME)
        else:
            print("no pyproject.toml")

    delete_directory(path_to_container)
    delete_not_necessary_licenses()


def git_clone_repo(repo_name):
    ssh = "git@github.com:kraussmaffei/" + repo_name + ".git"
    subprocess.run(
        "git clone " + ssh, shell=True, cwd=str(pathlib.Path.cwd() / "container")
    )


def git_checkout_tag(container, version):
    tag = "v" + version
    subprocess.run(
        "git -c advice.detachedHead=false checkout " + tag,
        shell=True,
        cwd=str(pathlib.Path.cwd() / "container" / container),
    )


def create_venv(container_name, path_to_venv, python_version, path_to_container):
    """

    :param container_name:
    :param path_to_venv:
    :param python_version:
    :param path_to_container:
    :return:
    """
    pyenv_path = Path(f"/home/azubi/.pyenv/versions/{python_version}")
    if not pyenv_path.is_dir():
        subprocess.run(
            f"~/.pyenv/bin/pyenv install {python_version}", shell=True, cwd=path_to_venv
        )
    print("pyenv virtualenv")
    venv_name = container_name + VENV_NAME
    subprocess.run(
        f"~/.pyenv/bin/pyenv virtualenv {python_version} {venv_name}", shell=True
    )
    print("pip install")
    pipinstall = path_to_container / container_name
    VIRTUAL_ENV = "/home/azubi/.pyenv/versions/3.8.16/envs/common-diagnostic_venv_licenses"
    subprocess.run(
        f"~/.pyenv/versions/{venv_name}/bin/pip install " + str(pipinstall), shell=True, env={"VIRTUAL_ENV":"/home/azubi/.pyenv/versions/3.8.16/envs/common-diagnostic_venv_licenses"}
    )
    #  subprocess.run('~/.pyenv/versions/' + repo_name + '/bin/python', shell=True)
    print("pip install done")


def delete_directory(path):
    try:
        shutil.rmtree(path)
    except OSError as e:
        print("Error: %s : %s" % (path, e.strerror))


def create_license_file(path_to_repo, venv_name):
    """

    :param path_to_repo:
    :param venv_name:
    :return:
    """
    path_to_pyenv = f"~/.pyenv/versions/{venv_name}/bin/pip"
    path_to_venv = f"/home/azubi/.pyenv/versions/3.8.16/envs/{venv_name}"

    print("output.txt")
    subprocess.run(
        f"pip-licenses --python={path_to_venv}/bin/python --with-license-file --with-notice-file --no-license-path --format=plain-vertical  > /home/azubi/PycharmProjects/edge-license-listing/output.txt",
        shell=True,
        cwd=path_to_repo,
        env={"VIRTUAL_ENV": "/home/azubi/.pyenv/versions/3.8.16/envs/common-diagnostic_venv_licenses"}
    )

    print("output2.json")
    subprocess.run(
        f"pip-licenses --python={path_to_venv}/bin/python --from=all --with-authors --format=json "
        "> ~/PycharmProjects/edge-license-listing/output2.json",
        shell=True,
        cwd=path_to_repo,
    )

    print("output0.txt")
    subprocess.run(
        f"pip-licenses --python={path_to_venv}/bin/python --with-description --with-system | grep pip > /home/azubi/PycharmProjects/edge-license-listing/output0.txt",
        shell=True,
    )


def delete_not_necessary_licenses():
    """

    :return:
    """
    licenses = {
        "Apache License": "true",
        "BSD License": "true",
        "GNU GPL": "false",
        "MIT License": "true",
        "UNKNOWN": "false",
    }
    allowed_licenses = [
        "Apache Software License",
        "MIT License",
        "BSD License",
        "Unilicense",
        "Historical Permission Notice and Disclaimer (HPND)",
    ]
    forbidden_licenses = ["GPL", "Mozilla Public License"]

    json_file = open("output2.json")
    json_data = json.load(json_file)
    for dict in json_data:
        keys = dict.keys()
        values = dict.values()
        if dict["License-Classifier"] == "UNKNOWN":
            print("WARNING\n")
        elif dict["License-Classifier"] not in allowed_licenses:
            print("NOT ALLOWED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(values)
            print("\n")


def clear_output_file(file_path):
    with open(file_path, "w") as file:
        file.write("")


def delete_venv(venv_name):
    subprocess.run(f"~/.pyenv/bin/pyenv virtualenv-delete -f {venv_name}", shell=True)


def get_python_version(pyproject_toml_path):
    """
    get python version from pyproject.toml
    :param pyproject_toml_path:
    :return:
    """
    return "3.8.16"
