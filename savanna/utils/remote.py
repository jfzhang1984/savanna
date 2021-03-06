# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib

import paramiko

from savanna import exceptions as ex
from savanna.utils import crypto
from savanna.utils.openstack import nova


def setup_ssh_connection(host, username, private_key):
    """Setup SSH connection to the host using username and private key."""
    if type(private_key) in [str, unicode]:
        private_key = crypto.to_paramiko_private_key(private_key)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, pkey=private_key)

    return ssh


def execute_command(ssh_connection, cmd, get_stderr=False,
                    raise_when_error=True):
    """Execute specified command remotely using existing ssh connection.

    Return exit code, stdout data and stderr data of the executed command.
    """
    chan = ssh_connection.get_transport().open_session()
    chan.exec_command(cmd)
    ret_code = chan.recv_exit_status()

    stdout = ''
    while chan.recv_ready():
        stdout += chan.recv(1024)

    stderr = ''
    while chan.recv_stderr_ready():
        stderr += chan.recv_stderr(1024)

    if ret_code and raise_when_error:
        raise ex.RemoteCommandException(cmd=cmd, ret_code=ret_code,
                                        stdout=stdout, stderr=stderr)

    if get_stderr:
        return ret_code, stdout, stderr

    else:
        return ret_code, stdout


def write_file_to(sftp, remote_file, data):
    """Create remote file using existing ssh connection and write the given
    data to it.
    """
    fl = sftp.file(remote_file, 'w')
    fl.write(data)
    fl.close()


def write_files_to(sftp, files):
    """Copy file->data dictionary in a single ssh connection.
    """
    for fl, data in files.iteritems():
        write_file_to(sftp, fl, data)


def read_file_from(sftp, remote_file):
    """Read remote file from the specified host and return given data."""
    fl = sftp.file(remote_file, 'r')
    data = fl.read()
    fl.close()
    return data


def replace_remote_string(ssh_connection, remote_file, old_str, new_str):
    """Replaces strings in remote file using sed command."""
    old_str = old_str.replace("\'", "\''")
    new_str = new_str.replace("\'", "\''")
    cmd = "sudo sed -i 's,%s,%s,g' %s" % (old_str, new_str, remote_file)
    execute_command(ssh_connection, cmd)


class InstanceInteropHelper(object):
    def __init__(self, instance):
        self.instance = instance

    def __enter__(self):
        self.bulk = BulkInstanceInteropHelper(self)
        return self.bulk

    def __exit__(self, *exc_info):
        self.bulk.close()

    def ssh_connection(self):
        username = nova.get_node_group_image_username(self.instance.node_group)
        return setup_ssh_connection(
            self.instance.management_ip, username,
            self.instance.node_group.cluster.private_key)

    def execute_command(self, cmd, get_stderr=False, raise_when_error=True):
        with contextlib.closing(self.ssh_connection()) as ssh:
            return execute_command(ssh, cmd, get_stderr, raise_when_error)

    def write_file_to(self, remote_file, data):
        with contextlib.closing(self.ssh_connection()) as ssh:
            return write_file_to(ssh.open_sftp(), remote_file, data)

    def write_files_to(self, files):
        with contextlib.closing(self.ssh_connection()) as ssh:
            return write_files_to(ssh.open_sftp(), files)

    def read_file_from(self, remote_file):
        with contextlib.closing(self.ssh_connection()) as ssh:
            return read_file_from(ssh.open_sftp(), remote_file)

    def replace_remote_string(self, remote_file, old_str, new_str):
        with contextlib.closing(self.ssh_connection()) as ssh:
            replace_remote_string(ssh, remote_file, old_str, new_str)


def get_remote(instance):
    return InstanceInteropHelper(instance)


class BulkInstanceInteropHelper(object):
    def __init__(self, helper):
        self.helper = helper
        self._ssh = None
        self._sftp = None

    def close(self):
        if self._sftp:
            self._sftp.close()
        if self._ssh:
            self._ssh.close()

    def ssh_connection(self):
        if not self._ssh:
            self._ssh = self.helper.ssh_connection()
        return self._ssh

    def sftp_connection(self):
        if not self._sftp:
            self._sftp = self.ssh_connection().open_sftp()
        return self._sftp

    def execute_command(self, cmd, get_stderr=False, raise_when_error=True):
        return execute_command(self.ssh_connection(), cmd, get_stderr,
                               raise_when_error)

    def write_file_to(self, remote_file, data):
        return write_file_to(self.sftp_connection(), remote_file, data)

    def write_files_to(self, files):
        return write_files_to(self.sftp_connection(), files)

    def read_file_from(self, remote_file):
        return read_file_from(self.sftp_connection(), remote_file)

    def replace_remote_string(self, remote_file, old_str, new_str):
        replace_remote_string(self.ssh_connection(), remote_file,
                              old_str, new_str)
