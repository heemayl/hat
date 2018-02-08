### HAT (Hyper-AT) is an one time run job scheduler for GNU/Linux, with an emphasis on usability. It is designed to be a direct replacement of `at` (`atq`, `atrm`), `batch`, and other such one time run task scheduling engines/toolsets.

Benefits of `hat`:

- Seconds resolution i.e. you can run job at the mentioned second
- Use your shell of choice; you're not bound to `/bin/sh`
- Job modification is supported; you can easily modify command, time of an enqueued job
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

# Job listing: --list/-l
% hatc -l
Job queue is empty

# `hatc --list` is the default
% hatc
Job queue is empty

# Job count: --count/-c
% hatc -c
0

# Job addition/scheduling: --add/-a
% hatc --add free 'now + 5 min'
{'msg': 'Done'}

% hatc -l
ID		    Time		Shell		Command
1	    2018-02-08T16:47:29		  -		free

% hatc -c
1

% hatc -a 'echo $PATH' 'tomorrow 14:40:30' bash
{'msg': 'Done'}

% hatc -l
ID		    Time		Shell		Command
1	    2018-02-08T16:47:29		  -		free
2	    2018-02-09T14:40:30		bash		echo $PATH

% hatc -c
2

# Job removal: --remove/-r
% hatc --remove 1
{'msg': 'Queued'}

% hatc -l
ID		    Time		Shell		Command
2           2018-02-09T14:40:30		bash		echo $PATH

% hatc -c
1

% hatc --remove 2
{'msg': 'Queued'}

% hatc -l
Job queue is empty

% hatc -c
0

% hatc -a free 'now +30 mins'
{'msg': 'Done'}

% hatc -l
ID		    Time	       Shell		Command
1	    2018-02-09T03:41:57		 -		free

# Job modification: --modify/-m
% hatc --modify 1 'free -m' _
{'msg': 'Done'}

% hatc -l
ID		    Time	       Shell		Command
1	    2018-02-09T03:41:57		 -		free -m

% hatc -m 1 _ 'today 14:30:42'
{'msg': 'Done'}

% hatc -l
ID     		    Time	       Shell		Command
1 	    2018-02-09T14:30:42		 -		free -m


```

---
