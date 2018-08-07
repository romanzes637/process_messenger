import argparse
import json
import os
import shlex
import socket
from pprint import pprint
from subprocess import Popen


class ProcessMessenger:
    def __init__(self, processes, mailing_list, n_log_lines, is_full_log, ssh):
        """
        Class for messaging processes states
        :param dict processes: {'pid': {'status': 1 (running) or 0 (done) or None, 'abs_log_path': 'path' or None,
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

    def check_processes(self):
        is_changed = False
        for pid in self.processes:
            status = self.processes[pid].get('status', 1)
            if status != 0:
                try:
                    os.kill(int(pid), 0)  # Check process running
                except OSError:
                    print('Done {}'.format(pid))
                    self.processes[pid]['status'] = 0
                    self.send_email(pid)
                    is_changed = True
        return is_changed

    get_mail_command = {
        'no_ssh_no_attachment': (lambda ssh, body, subject, attachment, recipient:
                                 'echo {} | mail -s {} {}'.format(body, subject, recipient)),
        'no_ssh_attachment': (lambda ssh, body, subject, attachment, recipient:
                              'echo {} | mail -s {} -a {} {}'.format(body, subject, attachment, recipient)),
        'ssh_attachment': (lambda ssh, body, subject, attachment, recipient:
                           'ssh {} echo {} | mail -s {} -a {} {}'.format(ssh, body, subject, attachment, recipient)),
        'ssh_no_attachment': (lambda ssh, body, subject, attachment, recipient:
                              'ssh {} echo {} | mail -s {} {}'.format(ssh, body, subject, recipient))
    }

    def send_email(self, pid):
        print('Mailing')
        print('Preparing')
        abs_log_path = self.processes[pid].get('abs_log_path', None)
        name = self.processes[pid].get('name', None)
        hostname = socket.gethostname()
        subject = 'Done_Host:{}_Name:{}_PID:{}'.format(hostname, name, pid)
        print('Subject: {}'.format(subject))
        body = ''
        attachment = None
        temp_log_path = None
        if abs_log_path is not None:
            if os.path.isfile(abs_log_path):
                body = 'abs_log_path:{}'.format(abs_log_path)
                if not self.is_full_log:
                    temp_log_path = os.path.abspath('process_messenger_temp_log_{}.txt'.format(pid))
                    lines = list()
                    with open(abs_log_path) as f:
                        for i, line in enumerate(reversed(f.readlines())):
                            if i < self.n_log_lines:
                                lines.append(line)
                    temp_log = str().join(lines)
                    with open(temp_log_path, 'w+') as af:
                        af.write(temp_log)
                    attachment = temp_log_path
                else:
                    attachment = abs_log_path
            else:
                print("Warning! {} log file doesn't exist".format(abs_log_path))
        print('Body: {}'.format(body))
        print('Attachment: {}'.format(attachment))
        print('Sending')
        if attachment is not None and self.ssh is not None:
            mail_type = 'ssh_attachment'
        elif attachment is None and self.ssh is not None:
            mail_type = 'ssh_no_attachment'
        elif attachment is not None and self.ssh is None:
            mail_type = 'no_ssh_attachment'
        elif attachment is None and self.ssh is None:
            mail_type = 'no_ssh_no_attachment'
        print('Mail type: {}'.format(mail_type))
        for email in self.mailing_list:
            recipient = email
            print(recipient)
            command = self.get_mail_command[mail_type](self.ssh, body, subject, attachment, recipient)
            split_command = shlex.split(command)
            # print(split_command)
            process = Popen(split_command)
            process.wait()
        if temp_log_path:
            os.remove(temp_log_path)
        print('Done mailing')


def main():
    print('Arguments')
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='path to config json file', default='process_messenger_config.json')
    parser.add_argument('-i', '--input', help='path to input json file')
    parser.add_argument('-p', '--pids', help='processes ids', nargs='+')
    parser.add_argument('-l', '--logs', help='processes logs paths', nargs='+')
    parser.add_argument('-n', '--names', help='processes names', nargs='+')
    args = parser.parse_args()
    print(args)
    # Get config
    # "input": "path to input json file",
    # "ssh": "username@host" or "host" or null,
    # "mailing_list": ["local-part@domain", ...],
    # "n_log_lines": int,
    # "full_log": bool
    with open(args.config) as f:
        config_args = json.load(f)
    print('Configs')
    pprint(config_args)
    # Get input from input file or from command line
    # "pid": {
    #   "abs_log_path": "abs path to process log file" or null,
    #   "status": 1 or 0 or null,
    #   "name": "process name" or null
    # }
    if args.input is None:
        input_file_path = config_args['input']
    else:  # if -i key
        input_file_path = args.input
    print('Input file: {}'.format(input_file_path))
    if args.pids is None:
        with open(input_file_path) as f:
            processes = json.load(f)
    else:  # if -p key
        processes = dict()
        for i, pid in enumerate(args.pids):
            processes[pid] = dict()
            if args.logs is not None:  # if -l key
                abs_log_path = os.path.expanduser(args.logs[i]) if i < len(args.logs) else None
                processes[pid]['abs_log_path'] = abs_log_path
            if args.names is not None:  # if -n key
                name = args.names[i] if i < len(args.names) else None
                processes[pid]['name'] = name
    print('Processes')
    pprint(processes)
    print('Initializing ProcessMessenger')
    pm = ProcessMessenger(
        processes, config_args['mailing_list'], config_args['n_log_lines'],
        config_args['full_log'], config_args['ssh'])
    all_done = False
    print('Start monitoring')
    while not all_done:  # Stop if all processes are done
        is_changed = pm.check_processes()  # Update processes statuses
        if is_changed:
            print('Updating input file')
            with open(input_file_path, 'w') as f:
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
