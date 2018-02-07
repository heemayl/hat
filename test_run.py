import datetime
import os
# import multiprocessing
import time
import json

# from lib.scheduler import Job
from lib.runner import BaseRunner



# from daemon import HatDaemon

DAEMON_IN = '/var/run/hatd/ipc/daemon_in.fifo'
DAEMON_OUT = '/var/run/hatd/ipc/daemon_out.fifo'


# These are server daemon and client codes...
# daemon = HatDaemon()
# daemon.start()
# print(daemon.status_verbose)
# print(daemon.pid)
BaseRunner.write_to_file(DAEMON_IN, json.dumps({
    'add_job': {
        'euid': os.geteuid(),
        'command': 'cat /etc/apg.conf',
        'time_': (datetime.datetime.now() + datetime.timedelta(minutes=1))
        .strftime('%Y-%m-%d %H:%M:%S'),
        # 'use_shell': True
    }
}), 'wt', True)


BaseRunner.write_to_file(DAEMON_IN, json.dumps({
    'add_job': {
        'euid': os.geteuid(),
        'command': 'caasdasdasd',
        'time_': (datetime.datetime.now() + datetime.timedelta(minutes=1))
        .strftime('%Y-%m-%d %H:%M:%S'),
        'use_shell': True
    }
}), 'wt', True)

BaseRunner.write_to_file(DAEMON_IN, json.dumps({
    'add_job': {
        'euid': os.geteuid(),
        'command': 'cat /etc/shadow',
        'time_': (datetime.datetime.now() + datetime.timedelta(minutes=2))
        .strftime('%Y-%m-%d %H:%M:%S'),
        # 'use_shell': True
    }
}), 'wt', True)

BaseRunner.write_to_file(DAEMON_IN, json.dumps({
    'add_job': {
        'euid': os.geteuid(),
        'command': 'bash -c "foo(){ echo HAT ;}; foo"',
        'time_': (datetime.datetime.now() + datetime.timedelta(minutes=4))
        .strftime('%Y-%m-%d %H:%M:%S'),
        'use_shell': True
    }
}), 'wt', True)

BaseRunner.write_to_file(DAEMON_IN, json.dumps({
    'remove_job': (1000, 4)
}), 'wt', True)

BaseRunner.write_to_file(DAEMON_IN, json.dumps({
    'jobcount': 1000
}), 'wt', True)

BaseRunner.write_to_file(DAEMON_IN, json.dumps({
    'joblist': 1000
}), 'wt', True)


# daemon.remove_job(1000, 8, 1)
# daemon.remove_job(1)

with open(DAEMON_OUT) as f:
    while True:
        for line in f:
            print(json.loads(line))
    
#    time.sleep(120)
#    daemon.stop()

# The runner object
# runner_ = BaseRunner()
# queue = runner_.get_queue()


# # Starting the runner
# # def runner_wraper(queue):
# #     while True:
# #         if runner_._running:
# #             item = queue.get()
# #             with open('/home/chayan/checking', 'a') as f:
# #                 f.write(str(queue) + 'dads')
# #             if isinstance(item, dict):
# #                 command = item['command']
# #                 time_ = item['time_']
# #                 Job(command, time_)
# #         else:
# #             with open('/home/chayan/checking', 'a') as f:
# #                 f.write('start')
# #             runner_.start()
# #         time.sleep(0.1)

# print(runner_.jobcount)
# proc = multiprocessing.Process(target=runner_.start)
# proc.start()
# print(proc.is_alive())

# #runner_.start()

# # Creating test jobs
# Job('cat /etc/shadow',
#     (datetime.datetime.now() + datetime.timedelta(minutes=1))
#     .strftime('%Y-%m-%d %H:%M:%S'))

# Job('cat /proc/uptime',
#     (datetime.datetime.now() + datetime.timedelta(minutes=1))
#     .strftime('%Y-%m-%d %H:%M:%S'))

# Job('no_such_command',
#     (datetime.datetime.now() + datetime.timedelta(minutes=5))
#     .strftime('%Y-%m-%d %H:%M:%S'))

# Job('whoami',
#     (datetime.datetime.now() + datetime.timedelta(minutes=10))
#     .strftime('%Y-%m-%d %H:%M:%S'))

# print(runner_.jobcount)

# # Creating test jobs
# queue.put_nowait({'command': 'cat /proc/meminfo',
#            'time_': (
#             datetime.datetime.now() + datetime.timedelta(minutes=1))
#            .strftime('%Y-%m-%d %H:%M:%S')})

# queue.put_nowait({'command': 'cat /proc/irq/default_smp_affinity',
#                   'time_': (
#                       datetime.datetime.now() + datetime.timedelta(minutes=2))
#                   .strftime('%Y-%m-%d %H:%M:%S'),
#                   'use_shell': True})

# # print(runner_.jobcount)

# time.sleep(140)
# print(runner_.jobcount)
# runner_.stop()
# time.sleep(2)
# print(runner_._running)
# print(proc.is_alive())


# # q.put('oooopsie poopsie',
# #       (datetime.datetime.now() + datetime.timedelta(minutes=1))
# #       .strftime('%Y-%m-%d %H:%M:%S'))

# # q.put('no_such_command',
# #       (datetime.datetime.now() + datetime.timedelta(minutes=5))
# #       .strftime('%Y-%m-%d %H:%M:%S'))

# # q.put('whoami',
# #       (datetime.datetime.now() + datetime.timedelta(minutes=10))
# #       .strftime('%Y-%m-%d %H:%M:%S'))

