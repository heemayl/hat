### HAT (Hyper-AT) is an one time run job scheduler for GNU/Linux, with an emphasis on usability. It is designed to be a direct replacement of `at` (`atq`, `atrm`), `batch`, and other such one time run task scheduling engines/toolsets.

Benefits of `hat`:

- Seconds resolution i.e. you can run job at the mentioned second
- Use your shell of choice; you're not bound to `/bin/sh`
- Flexible datetime specifications, see https://github.com/heemayl/humantime-epoch-converter
- Will run a scheduled job later when the computer was off at that time, so no job will be missed
- User specific jobs, secured approach
- User based logging, all logs from jobs of a user go in `~/.hatd/logs/`
- All-in-one i.e. no separate tool based on job or pattern
- Easy to use

---

# Installation:

1. Clone or download the repository

2. Run the `install.sh` script as superuser

3. Check `hatc --help`

**N.B** The userspace command is `hatc` -- the only thing you should need.

---

## Example workflow:

```bash
% hatc -l
[]

% hatc -c
0

% hatc --add free 'tomorrow 15:47:57'

% hatc -l
[
    [
        "1",
	{
	    "command": "free",
	    "job_run_at": 1518040077,
	    "use_shell": false
	}
    ]
]

% hatc -c
1

% hatc -a 'echo $PATH' 'now + 3 mins' bash
{'msg': 'Done'}

% hatc -l
[
    [
        "1",
	{
	    "command": "free",
	    "job_run_at": 1518040077,
	    "use_shell": false
	}
    ],
    [
        "2",
	{
	    "command": "bash -c \"echo $PATH\"",
	    "job_run_at": 1517999620,
	    "use_shell": "bash"
	}
    ]
]

% hatc -c
2

% hatc --remove 1
{'msg': 'Queued'}

% hatc -l
[
    [
        "2",
        {
            "command": "bash -c \"echo $PATH\"",
	    "job_run_at": 1517999620,
	    "use_shell": "bash"
	}
    ]
]

% hatc -c
1

```

---
