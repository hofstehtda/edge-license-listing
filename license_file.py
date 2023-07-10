import json
import pathlib
import shutil
from typing import Tuple, List
from pathlib import Path

import re
import subprocess

VENV_NAME = "_venv_licenses"
PATH_TO_PYENV_FOLDER = "/home/azubi"
codeartifact = 304998364617

DOCKER_NAME_VERSION_PATTERN = fr"image: {codeartifact}.dkr.ecr.eu-central-1.amazonaws.com/([a-z-]+):(\d+\.\d+\.\d+)"


def get_containers_and_version(file_path: Path) -> List[Tuple[str, str]]:
    """
    opens docker-compose.yaml and returns name and version as a list
    :param file_path: file path to yaml file
    :return: list
    """
    yaml_content = file_path.read_text()

    container_list = re.findall(DOCKER_NAME_VERSION_PATTERN, yaml_content)

    return container_list


def generate_license_file() -> None:
    """
    generates output file with licenses
    :param
    :return:
    """
    current_directory = Path(__file__).parent
    path_to_container = current_directory / "container"

    delete_directory(path_to_container)
    Path.mkdir(Path.cwd() / "container")

    clear_output_file(current_directory / "output.txt")
    clear_output_file(current_directory / "output0.txt")
    clear_output_file(current_directory / "output2.json")
    containers = get_containers_and_version(
        current_directory / "yml_files" / "docker-compose.yml"
    )

    for container, version in containers:
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


# delete_not_necessary_licenses()


def git_clone_repo(repo_name):
    ssh = "git@github.com:kraussmaffei/" + repo_name + ".git"
    subprocess.run(
        "git clone " + ssh, shell=True, cwd=str(pathlib.Path.cwd() / "container")
    )


def git_checkout_tag(container, version):
    # TODO: checken ob der befehl fehlschägt, wenn ja nochmal ohne "v" versuchen
    tag = "v" + version
    subprocess.run(
        "git -c advice.detachedHead=false checkout " + tag,
        shell=True,
        cwd=str(pathlib.Path.cwd() / "container" / container),
    )
    print('v')
    subprocess.run(
        "git -c advice.detachedHead=false checkout " + version,
        shell=True,
        cwd=str(pathlib.Path.cwd() / "container" / container),
    )
    print('tag')


def create_venv(container_name, path_to_venv, python_version, path_to_container):
    """

    :param container_name:
    :param path_to_venv:
    :param python_version:
    :param path_to_container:
    :return:
    """
    pyenv_path = Path(f"{PATH_TO_PYENV_FOLDER}/.pyenv/versions/{python_version}")
    if not pyenv_path.is_dir():
        subprocess.run(
            f"~/.pyenv/bin/pyenv install {python_version}",
            shell=True,
            cwd=path_to_venv,
        )
    print("pyenv virtualenv")
    venv_name = container_name + VENV_NAME
    subprocess.run(
        f"~/.pyenv/bin/pyenv virtualenv {python_version} {venv_name}", shell=True
    )

    venv_path = Path(__file__).parent / "virtual_environments/"  # ????????????
    # subprocess.run(f"python -m venv {venv_path}")

    print("pip install")
    pipinstall = path_to_container / container_name
    venv_path = "/home/azubi/.pyenv/versions/3.8.16/envs/" + venv_name
    subprocess.run(
        f"/home/azubi/.pyenv/versions/3.8.16/envs/{venv_name}/bin/pip install "
        + str(pipinstall),
        shell=True,
        env={
            "VIRTUAL_ENV": venv_path
        },
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
        f"pip-licenses --python={path_to_venv}/bin/python --with-license-file --with-notice-file --no-license-path --format=plain-vertical  >> /home/azubi/PycharmProjects/edge-license-listing/output.txt",
        shell=True,
        cwd=path_to_repo,
    )
    print("output.txt created")

    subprocess.run(
        f"pip-licenses --python={path_to_venv}/bin/python --from=all --with-description --format=json  >> /home/azubi/PycharmProjects/edge-license-listing/output2.json",
        shell=True,
        cwd=path_to_repo,
    )
    print("output2.json created")


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
        values = dict.values()
        if dict["License-Classifier"] == "UNKNOWN":
            print("WARNING")
        elif dict["License-Classifier"] not in allowed_licenses:
            print("NOT ALLOWED!")
            print(values)


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
