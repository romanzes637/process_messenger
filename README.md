# process_messenger
Messaging processes states by email

## Mail format:
Subject: Done_host:host_name:name_pid:pid

Body: log_path:pid[log_path] (see below)

Attachment: n_log_lines or full log from log_path (see below)

## Write input file with processes for monitoring processes.json in the format [optional]:
```
{
  "pid" {
    ["status": 1 or 0,] (1 - running, 0 - done)
    ["name": "process name",]
    ["log_path": "process log absolute path"]
  },
  "pid_2 {
  },
  "pid_n" {
  }
}
```

## Change config file process_messenger_config.json parameters:
```
{
  "input": "processes.json", (input file relative path to process_messenger.py, see above)
  "ssh": "username@host" or "host" or null, (ssh tunnling, null - not use)
  "mailing_list": ["local-part@domain", "local-part_2@domain"],
  "n_log_lines": 10, (number of last log lines to email attachment)
  "full_log": false (attach full log to email if exists),
  "sender": "local-part@domain"
}
```

## Run
## Note: script update input file (default: processes.json) with current processes states
```
python process_messenger.py
```

## Variant: use command line arguments:
```
-c  config file absolute path
-i  input file absolute path
-p  pid pid_2 pid_n
-l  log_path log_path_2 log_path_n (processes logs absolute paths)
-n  name name_2 name_n
```

