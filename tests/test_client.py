#!/usr/bin/env python3

# Test case(s) for the hat client -- `client.py`

import os
import sys
import unittest

# Inserting the dir in `sys.path` at index 0
sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), 'hat'))

import client


class ClientTest(unittest.TestCase):
    '''Testing various functionalities of the hat client.'''
    def test_check_daemon_process(self):
        '''Checking the check_daemon_process func.'''
        pid_file = '/var/run/hatd/hatd.pid'
        if os.path.isfile(pid_file):
            self.assertTrue(client.check_daemon_process(pid_file))
        else:
            self.assertFalse(client.check_daemon_process(pid_file))

    def test_argument_daemon_response(self):
        '''Checking argument_serializer func,
        and daemon response after sending data.
        '''
        # Argument input-output map for argument_serializer
        args_dict_all = {
            'joblist': {
                'input': {
                    'joblist': True
                },
                'output': 1  # length
            },
            'jobcount': {
                'input': {
                    'jobcount': True
                },
                'output': 1
            },
            'add_job': {
                'input': {
                    'add_job': ['whoami', 'now + 3 mins', 'bash']
                },
                'output': 4
            },
            'remove_job': {
                'input': {
                    'remove_job': [1, 2]
                },
                'output': 3
            }
        }
        for arg, val in args_dict_all.items():
            out = client.argument_serializer(val['input'])
            # Check args serializer
            self.assertTrue((out[0] == arg) and (len(out) == val['output']),
                            'Error on arg: {}'.format(arg))
            data = client.SendReceiveData(out)
            data.check_get_send()
            received = data.receive_from_daemon()
            # daemon returned something or not
            self.assertIsNotNone(received, 'No data for: {}'.format(arg))


if __name__ == '__main__':
    unittest.main()

