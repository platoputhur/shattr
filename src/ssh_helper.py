import logging
import os
from paramiko.client import SSHClient, RSAKey
from paramiko import AutoAddPolicy


class SSHHelper:
    def __init__(self, host, username=None, pkey_path=None):
        self.client = SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(AutoAddPolicy)
        username = username if username else os.getlogin()
        if not pkey_path:
            homedir = os.path.expanduser('~')
            pkey = RSAKey.from_private_key_file(f"{homedir}/.ssh/id_rsa")
        else:
            pkey = RSAKey.from_private_key_file(pkey_path)
        self.client.connect(host, username=username, pkey=pkey)

    def close_connection(self):
        self.client.close()

    def run_ssh_command(self, command):
        _, stdout, stderr = self.client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        stdout.channel.recv_exit_status()
        stderr.channel.recv_exit_status()
        return _, output, error

    def entity_exists_in_ssh(self, filepath):
        command = f"test -e {filepath} && echo 1"
        stdin, output, stderr = self.run_ssh_command(command)
        if not output:
            return False
        else:
            return True

    def find_entity_in_ssh_server(self, search_path, entity_name, entity_type="f"):
        command = f"find {search_path} -type {entity_type} -name {entity_name}"
        stdin, output, stderr = self.run_ssh_command(command)
        if not output:
            logging.getLogger().error(f"Couldn't find {entity_name} in the master node")
        else:
            lines = output.split("\n")
            path_with_filename = lines[0].split("./")[1]
            return os.path.join(search_path, path_with_filename)

    def find_entity_and_run_command_via_ssh(
            self,
            entity_full_path=None,
            search_path=None,
            entity_type="f",
            command_with_params=None,
            command_suffix=None
    ):
        error_message = ""
        if search_path is not None:
            entity_name = os.path.basename(entity_full_path)
            # Check if file exists
            if not self.entity_exists_in_ssh(entity_full_path):
                logging.getLogger().info(
                    f"Couldn't find {entity_name} in the default location, trying to search for '{entity_name}'."
                )
                entity_full_path = self.find_entity_in_ssh_server(search_path, entity_name, entity_type=entity_type)
        if command_suffix:
            command = f"{command_with_params} {entity_full_path}{command_suffix}"
        else:
            command = f"{command_with_params} {entity_full_path}"
        stdin, output, stderr = self.run_ssh_command(command)
        if stderr:
            if "Permission denied" in stderr:
                command = f"sudo {command}"
                stdin, output, stderr = self.run_ssh_command(command)
        if not stderr and output:
            return output, error_message
        else:
            error_message = f"Running stat on {entity_full_path} failed with error: {stderr}"
            return None, error_message

    def find_entity_ownership_via_ssh(self, entity_full_path, search_path=None):
        command_with_params = "stat -c %U:%G"
        result, error = self.find_entity_and_run_command_via_ssh(
            search_path=search_path,
            entity_full_path=entity_full_path,
            command_with_params=command_with_params
        )
        if error:
            if "Permission denied" in error:
                command_with_params = "sudo stat -c %U:%G"
                result, error = self.find_entity_and_run_command_via_ssh(
                    search_path=search_path,
                    entity_full_path=entity_full_path,
                    command_with_params=command_with_params
                )
        if error:
            logging.getLogger().info(error)
            return None
        else:
            return result.split("\n")[0]

    def find_entity_permissions_via_ssh(self, entity_full_path, search_path=None):
        command_with_params = "stat -c %a"
        result, error = self.find_entity_and_run_command_via_ssh(
            search_path=search_path,
            entity_full_path=entity_full_path,
            command_with_params=command_with_params
        )
        if error:
            if "Permission denied" in error:
                command_with_params = "sudo stat -c %a"
                result, error = self.find_entity_and_run_command_via_ssh(
                    search_path=search_path,
                    entity_full_path=entity_full_path,
                    command_with_params=command_with_params
                )
        if error:
            logging.getLogger().info(error)
            return None
        else:
            return result.split("\n")[0]

    def run_command_with_bash_c(self, command_with_params, entity_full_path):
        full_command = f"bash -c '{command_with_params} {entity_full_path}'"
        stdin, output, stderr = self.run_ssh_command(full_command)
        if stderr:
            if "Permission denied" in stderr:
                full_command = f"sudo bash -c '{command_with_params}'"
                stdin, output, stderr = self.run_ssh_command(full_command)
        if stderr:
            error_message = f"Running stat on {entity_full_path} failed with error: {stderr}"
            logging.getLogger().info(error_message)
            return None
        else:
            return [item for item in output.split("\n") if item]

    def find_ownership_of_contents_of_a_dir(self, entity_full_path):
        command_with_params = f"stat -c %U:%G {entity_full_path}"
        return self.run_command_with_bash_c(command_with_params, entity_full_path)

    def find_permissions_of_contents_of_a_dir(self, entity_full_path):
        command_with_params = f"stat -c %a {entity_full_path}"
        return self.run_command_with_bash_c(command_with_params, entity_full_path)
