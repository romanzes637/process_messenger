# process_messenger
Messaging processes states by email

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
  "input": "processes.json", (file with processes, see above)
  "ssh": "username@host" or "host" or null, (ssh tunnling, null - not use)
  "mailing_list": ["local-part@domain", "local-part_2@domain"],
  "n_log_lines": 10, (number of log last lines to email attachment)
  "full_log": false (attach full log to email if exists)
}
```

## Run
```
python process_messenger.py
```
