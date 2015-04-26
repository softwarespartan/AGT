import boto
import pyDate

from boto.dynamodb2.table import Table

conn = boto.connect_dynamodb();

device_data = conn.get_table('com.fontus.device.data');

devid = '000000005a893855';

items = device_data.get_item(hash_key=devid,range_key=2013.44772451);

for i in items:
    print i,items[i];
    
    
#items = device_data.scan();

#for i in items:
#    print i

from boto.dynamodb.condition import LT;
items = device_data.query(devid,range_key_condition=LT(2014))

with open('/Users/abelbrown/'+devid+'.dat','w') as f:
    
    for i in items:
        line = str(i['dt'])+','+str(i['meas'])+'\n';
        f.write(line);
    
print items.count