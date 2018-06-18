import boto

conn = boto.connect_ec2()
print conn
spotRequests = conn.get_all_spot_instance_requests()
for sr in spotRequests:
    print sr