import logging
import re

from src.config import get_config
from src.ssh_helper import SSHHelper

ssh_cli = None
def main():
    logging.basicConfig(level="WARNING")
    host = get_config("SSH_SERVER_IP")
    username = get_config("SSH_USERNAME")
    pkey_path = get_config("SSH_PKEY_PATH")
    if not host or not username or not pkey_path:
        logging.getLogger().error("One of the envs required for ssh connection is not set."
                                    "Required ENVs: SSH_SERVER_IP, SSH_USERNAME, SSH_PKEY_PATH"
                                    ". Set these to run the tests.")
        ssh_cli = SSHHelper(host, username=username, pkey_path=pkey_path)
    print(get_file_contents())

def get_file_contents():
    required_file_path = "/etc/ca-certificates.conf"
    command_with_params = "cat"
    result, error_message = ssh_cli.find_entity_and_run_command_via_ssh(
        entity_full_path=required_file_path,
        entity_type="f",
        command_with_params=command_with_params,
    )
    if error_message:
        logging.getLogger().error(error_message)
    return result


def find_file_and_get_file_permissions():
    search_path = "/etc/"
    filepath = "/etc/ca-certificates.conf"
    result = ssh_cli.find_entity_permissions_via_ssh(
        search_path=search_path,
        entity_full_path=filepath,
    )
    return result


def find_file_and_get_file_ownership():
    search_path = "/etc/"
    filepath = "/etc/ca-certificates.conf"
    result = ssh_cli.find_entity_ownership_via_ssh(
        search_path=search_path,
        entity_full_path=filepath,
    )
    return result


def get_dir_content_permissions():
    dir_path = "/etc/"
    result = ssh_cli.find_permissions_of_contents_of_a_dir(
        entity_full_path=dir_path,
    )
    return result


def get_dir_content_ownership():
    search_path = "/etc/"
    dir_path = "/etc/"
    result = ssh_cli.find_ownership_of_contents_of_a_dir(
        entity_full_path=dir_path,
    )
    return result
