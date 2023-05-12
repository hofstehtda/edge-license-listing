import json
import os
import pathlib
import shutil
from typing import Dict
from pathlib import Path

import yaml
import re
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
    path_to_container = "/home/azubi/PycharmProjects/edge-license-listing/container/"
    path_to_venv = "~/.pyenv/versions/"

    delete_directory(path_to_container)
    Path.mkdir(Path.cwd() / "container")

    clear_output_file('/home/azubi/PycharmProjects/edge-license-listing/output.txt')
    clear_output_file('/home/azubi/PycharmProjects/edge-license-listing/output0.txt')
    clear_output_file('/home/azubi/PycharmProjects/edge-license-listing/output1.txt')
    clear_output_file('/home/azubi/PycharmProjects/edge-license-listing/output2.json')
    clear_output_file('/home/azubi/PycharmProjects/edge-license-listing/output3.txt')
    clear_output_file('/home/azubi/PycharmProjects/edge-license-listing/output4.txt')
    clear_output_file('/home/azubi/PycharmProjects/edge-license-listing/output5.txt')
    clear_output_file('/home/azubi/PycharmProjects/edge-license-listing/output6.txt')
    containers = get_containers_and_version(
        "/home/azubi/PycharmProjects/edge-license-listing/yml_files/docker-compose.yml")

    for container, version in containers.items():
        git_clone_repo(container)
        git_checkout_tag(container, version)
        pyproject_toml_path = Path(
            path_to_container + container + "/pyproject.toml")
        if pyproject_toml_path.exists():
            python_version = get_python_version(pyproject_toml_path)
            create_venv(container, path_to_container + container, python_version, path_to_container)
            create_license_file(path_to_container + container)
            delete_venv(container + "_venv", path_to_venv + container, python_version)
        else:
            print('no pyproject.toml')

    delete_directory(path_to_container)
    delete_not_necessary_licenses()


def git_clone_repo(repo_name):
    ssh = "git@github.com:kraussmaffei/" + repo_name + ".git"
    subprocess.run('git clone ' + ssh, shell=True, cwd=str(pathlib.Path.cwd() / "container"))


def git_checkout_tag(container, version):
    tag = "v" + version
    subprocess.run("git checkout " + tag, shell=True, cwd=str(pathlib.Path.cwd() / "container" / container))


def create_venv(container_name, path_to_venv, python_version, path_to_container):
    pyenv_path = Path(f"/home/azubi/.pyenv/versions/{python_version}")
    if not pyenv_path.is_dir():
        subprocess.run('~/.pyenv/bin/pyenv install ' + python_version, shell=True, cwd=path_to_venv)
    print("pyenv virtualenv")
    venv_name = container_name + "_venv"
    subprocess.run('~/.pyenv/bin/pyenv virtualenv ' + python_version + ' ' + venv_name, shell=True)
    print('pip install')
    pipinstall = path_to_container + container_name
    subprocess.run(f"~/.pyenv/versions/{venv_name}/bin/pip install " + pipinstall, shell=True)
    #  subprocess.run('~/.pyenv/versions/' + repo_name + '/bin/python', shell=True)


def delete_directory(path):
    try:
        shutil.rmtree(path)
    except OSError as e:
        print("Error: %s : %s" % (path, e.strerror))


def create_license_file(path_to_repo):
    subprocess.run('pip-licenses --with-license-file --with-notice-file --no-license-path --format=plain-vertical  '
                   '> /home/azubi/PycharmProjects/edge-license-listing/output.txt',
                   shell=True,
                   cwd=path_to_repo)
    subprocess.run('pip-licenses --with-license-file --with-notice-file --no-license-path --format=json  '
                   '> /home/azubi/PycharmProjects/edge-license-listing/output0.txt',
                   shell=True,
                   cwd=path_to_repo)
    subprocess.run('pip-licenses --format=plain-vertical --with-license-file --no-license-path  '
                   '> /home/azubi/PycharmProjects/edge-license-listing/output1.txt',
                   shell=True,
                   cwd=path_to_repo)
    subprocess.run('pip-licenses --from=all --with-authors --format=json '
                   '> /home/azubi/PycharmProjects/edge-license-listing/output2.json',
                   shell=True,
                   cwd=path_to_repo)
    subprocess.run('pip-licenses --order=license '
                   '> /home/azubi/PycharmProjects/edge-license-listing/output3.txt',
                   shell=True,
                   cwd=path_to_repo)
    subprocess.run('pip-licenses --from=all --with-authors '
                   '> /home/azubi/PycharmProjects/edge-license-listing/output4.txt',
                   shell=True,
                   cwd=path_to_repo)
    subprocess.run('pip-licenses --with-urls '
                   '> /home/azubi/PycharmProjects/edge-license-listing/output5.txt',
                   shell=True,
                   cwd=path_to_repo)
    subprocess.run('pip-licenses --with-description '
                   '> /home/azubi/PycharmProjects/edge-license-listing/output6.txt',
                   shell=True,
                   cwd=path_to_repo)


def delete_not_necessary_licenses():
    licenses = {
        "Apache License": "true",
        "BSD License": "true",
        "GNU GPL": "false",
        "MIT License": "true",
        "UNKNOWN": "false"
    }
    allowed_licenses = ['Apache Software License', 'MIT License', 'BSD License', 'Unilicense', 'Historical Permission Notice and Disclaimer (HPND)']
    forbidden_licenses = ['GPL', 'Mozilla Public License']

    json_file = open('output2.json')
    json_data = json.load(json_file)
    for dict in json_data:
        keys = dict.keys()
        #  print(keys)
        values = dict.values()
        #  print(values)
        if dict["License-Classifier"] == "UNKNOWN":
            print('WARNING\n')
        elif dict["License-Classifier"] not in allowed_licenses:
            print('NOT ALLOWED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(values)
            print('\n')


def clear_output_file(file_path):
    with open(file_path, 'w') as file:
        file.write('')


def delete_venv(venv_name, path_to_venv, python_version):
    #subprocess.run('~/.pyenv/bin/pyenv deactivate ' + python_version + '/envs/' + venv_name, shell=True, cwd=path_to_venv)
    path_to_venv = f"/home/azubi/.pyenv/versions/3.8.16/envs/{venv_name}"
    path_to_shortcut = f"/home/azubi/.pyenv/versions/ {venv_name}"
    #subprocess.run('ls -l ' + path_to_shortcut)
    """if os.path.isfile(path_to_shortcut):
        os.remove(path_to_shortcut)
    else:
        print("delete venv")
        print("Error: %s file not found" % path_to_shortcut)"""
    delete_directory(path_to_venv)


def get_python_version(pyproject_toml_path):
    return "3.8.16"
