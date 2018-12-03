import argparse
import json
import os
import shlex
import socket
from pprint import pprint
from subprocess import Popen
import sys


class ProcessMessenger:
    def __init__(self, processes, mailing_list, n_log_lines, is_full_log, ssh, sender):
        """
        Class for messaging processes states
        :param dict processes: {'pid': {'status': 1 (running) or 0 (done) or None, 'log_path': 'path' or None,
        'name': 'process name' or None}}
        :param list mailing_list: emails ['local-part@domain', ...]
        :param int n_log_lines: number of lines from log end to email
        :param bool is_full_log: If True attach full log to email (Warning: Log may be too large!)
        :param str ssh: username@host or host or None
        """
        self.processes = processes
        self.mailing_list = mailing_list
        self.n_log_lines = n_log_lines
        self.is_full_log = is_full_log
        self.ssh = ssh
        self.sender = sender

    def check_processes(self):
        is_changed = False
        for pid in self.processes:
            status = self.processes[pid].get('status', 1)
            if status != 0:
                try:
                    os.kill(int(pid), 0)  # Check process running
                except OSError:
                    print('Done {0}'.format(pid))
                    self.processes[pid]['status'] = 0
                    self.send_email(pid)
                    is_changed = True
        return is_changed

    get_mail_command = {
        'no_ssh_no_attachment': (lambda ssh, body, subject, attachment, sender, recipient:
                                 'echo {0} | mail -s {1} -r {2} {3}'.format(
                                     body, subject, sender, recipient)),
        'no_ssh_attachment': (lambda ssh, body, subject, attachment, sender, recipient:
                              'echo {0} | mail -s {1} -a {2} -r {3} {4}'.format(
                                  body, subject, attachment, sender, recipient)),
        'ssh_attachment': (lambda ssh, body, subject, attachment, sender, recipient:
                           'ssh {0} echo {1} | mail -s {2} -a {3} -r {4} {5}'.format(
                               ssh, body, subject, attachment, sender, recipient)),
        'ssh_no_attachment': (lambda ssh, body, subject, attachment, sender, recipient:
                              'ssh {0} echo {1} | mail -s {2} -r {3} {4}'.format(
                                  ssh, body, subject, sender, recipient))
    }

    def send_email(self, pid):
        print('Mailing')
        print('Preparing')
        log_path = self.processes[pid].get('log_path', None)
        name = self.processes[pid].get('name', None)
        hostname = socket.gethostname()
        subject = 'Done_host:{0}_name:{1}_pid:{2}'.format(hostname, name, pid)
        print('Subject: {0}'.format(subject))
        attachment = None
        temp_log_path = None
        body = str()
        if log_path is not None:
            body = 'log_path:{0}'.format(log_path)
            if not self.is_full_log:
                temp_log_path = os.path.abspath('process_messenger_temp_log_{0}.txt'.format(pid))
                lines = list()
                with open(log_path) as f:
                    for i, line in enumerate(reversed(f.readlines())):
                        if i < self.n_log_lines:
                            lines.append(line)
                temp_log = str().join(lines)
                with open(temp_log_path, 'w+') as af:
                    af.write(temp_log)
                attachment = temp_log_path
            else:
                attachment = log_path
        print('Body: {0}'.format(body))
        print('Attachment: {0}'.format(attachment))
        print('Sending')
        if attachment is not None and self.ssh is not None:
            mail_type = 'ssh_attachment'
        elif attachment is None and self.ssh is not None:
            mail_type = 'ssh_no_attachment'
        elif attachment is not None and self.ssh is None:
            mail_type = 'no_ssh_attachment'
        elif attachment is None and self.ssh is None:
            mail_type = 'no_ssh_no_attachment'
        print('Mail type: {0}'.format(mail_type))
        for email in self.mailing_list:
            recipient = email
            print(recipient)
            command = self.get_mail_command[mail_type](self.ssh, body, subject, attachment, self.sender, recipient)
            split_command = shlex.split(command)
            # print(split_command)
            process = Popen(split_command)
            process.wait()
        if temp_log_path is not None:
            os.remove(temp_log_path)
        print('Done mailing')


def check_file(path):
    """
    Check path on the existing file in the order:
    0. If file at path
    1. Else if file at relative to current working directory path
    2. Else if file at relative to running script directory path
    3. Else if file at relative to running script directory path with eliminating all symbolics links (real)
    -1. Else no file
    :param str path:
    :return dict: {'type': int, 'path': str}
    """
    # Expand path
    path_expand_vars = os.path.expandvars(path)
    path_expand_vars_user = os.path.expanduser(path_expand_vars)
    # Get directories
    wd_path = os.getcwd()
    script_dir_path = os.path.dirname(os.path.abspath(__file__))
    # Set paths to file check
    clear_path = path_expand_vars_user
    rel_wd_path = os.path.join(wd_path, path_expand_vars_user)
    rel_script_path = os.path.join(script_dir_path, path_expand_vars_user)
    real_rel_script_path = os.path.realpath(rel_script_path)
    # Check on file:
    result = dict()
    if os.path.isfile(clear_path):
        result['type'] = 0
        result['path'] = clear_path
    elif os.path.isfile(rel_wd_path):
        result['type'] = 1
        result['path'] = rel_wd_path
    elif os.path.isfile(rel_script_path):
        result['type'] = 2
        result['path'] = rel_script_path
    elif os.path.isfile(real_rel_script_path):
        result['type'] = 3
        result['path'] = real_rel_script_path
    else:  # No file
        result['type'] = -1
        result['path'] = path
    return result


def main():
    print('Python: {0}'.format(sys.executable))
    print('Script: {0}'.format(__file__))
    print('Working Directory: {0}'.format(os.getcwd()))
    print('Command Line Arguments:')
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='path to config json file', default='process_messenger_config.json')
    parser.add_argument('input', help='path to input json file', nargs='?', default=None)
    #parser.add_argument('-i', '--input', help='path to input json file')
    parser.add_argument('-p', '--pids', help='processes ids', nargs='+')
    parser.add_argument('-l', '--logs', help='processes logs paths', nargs='+')
    parser.add_argument('-n', '--names', help='processes names', nargs='+')
    args = parser.parse_args()
    print(args)
    # Config
    result = check_file(args.config)
    config_path = result['path']
    print('Config: {0}'.format(config_path))
    with open(config_path) as f:
        config_args = json.load(f)
    pprint(config_args)
    # Input
    if args.input is None:
        result = check_file(config_args['input'])
        input_path = result['path']
    else:
        print('-input presented -> override config input')
        result = check_file(args.input)
        input_path = result['path']
    print('Input: {0}'.format(input_path))
    if args.pids is None:
        with open(input_path) as f:
            processes = json.load(f)
        # Check log_paths:
        for i, pid in enumerate(processes):
            log_path = processes[pid].get('log_path', None)
            if log_path is not None:
                result = check_file(log_path)
                if result['type'] >= 0:
                    processes[pid]['log_path'] = result['path']
    else:
        print('-p key presented -> override input pids')
        processes = dict()
        for i, pid in enumerate(args.pids):
            processes[pid] = dict()
            if args.logs is not None:
                print('-l key presented -> override input pids logs')
                log_path = args.logs[i] if i < len(args.logs) else None
                if log_path is not None:
                    result = check_file(log_path)
                    if result['type'] >= 0:
                        processes[pid]['log_path'] = result['path']
            if args.names is not None:
                print('-n key presented -> override input pids names')
                name = args.names[i] if i < len(args.names) else None
                processes[pid]['name'] = name
    pprint(processes)
    print('Initializing ProcessMessenger')
    pm = ProcessMessenger(
        processes, config_args['mailing_list'], config_args['n_log_lines'],
        config_args['full_log'], config_args['ssh'], config_args['sender'])
    all_done = False
    print('Start monitoring')
    while not all_done:  # Stop if all processes are done
        is_changed = pm.check_processes()  # Update processes statuses
        if is_changed:
            print('Updating input file')
            with open(input_path, 'w') as f:
                json.dump(pm.processes, f, indent=2)
            print('Done updating input file')
        all_done = True
        for pid in pm.processes:
            status = pm.processes[pid].get('status', 1)
            if status == 1:
                all_done = False
                break
    print('End monitoring')


if __name__ == '__main__':
    main()
