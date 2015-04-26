import boto, datetime, time


# Details of instance & time range you want to find spot prices for
instanceType = 'm3.2xlarge'
start_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z");
aZ = 'us-east-1d'

# Connect to EC2
conn = boto.connect_ec2()

# Get prices for instance, AZ and time range
prices = conn.get_spot_price_history(instance_type=instanceType,start_time=startTime,availability_zone=aZ,product_description='Linux/UNIX')

for p in prices:
    print p
