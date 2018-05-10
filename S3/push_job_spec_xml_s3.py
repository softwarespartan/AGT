#!/usr/local/bin/python

import os;

JOB_QUEUE = 'com_widelane_jobs';

ACCESS_KEY = 'AKIAJFBQAW7QL44GEG7A'
SECRET_KEY = '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'

from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message


def main():
    # create a connection to SQS
    conn = SQSConnection(ACCESS_KEY, SECRET_KEY);

    # ask for the JOB_QUEUE
    q = conn.get_queue(JOB_QUEUE);

    # create a new message
    m = Message();

    m.set_body(os.sys.stdin.read());

    # publish the message to SQS
    q.write(m);


if __name__ == "__main__":
    main()