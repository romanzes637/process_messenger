# process_messenger
Messaging processes states by email

## Mail format:
Subject: Done_Host:host_Name:name_PID:pid

Body: abs_log_path:abs_log_path (see below)

Attachment: n_log_lines or full log from abs_log_path (see below)

## Write processes for monitoring to processes.json in the format [optional]:
```
{
  "pid" {
    ["status": 1 or 0,] (1 - running, 0 - done)
    ["name": "process_name",]
    ["abs_log_path": "process absolute_log_path"]
  },
  "pid_2 {
  },
  "pid_n" {
  }
}
```

## Change process_messenger_config.json parameters:
```
{
  "input": "processes.json", (input file with processes, see above)
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
-c  config_file_path
-p  pid pid_2 pid_n
-l  abs_log_path abs_log_path_2 abs_log_path_n
-n  name name_2 name_n
```

