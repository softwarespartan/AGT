
import threading
import datetime

class ThreadExample(threading.Thread):
    def run(self):
        now = datetime.datetime.now()
        print '%s says Hello World at time: %s ' % (self.getName(), now)

for i in range(20):
    t = ThreadExample()
    t.start()
