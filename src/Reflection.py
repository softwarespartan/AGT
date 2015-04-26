

URL = 'http://169.254.169.254/latest/meta-data/';

import boto, datetime, subprocess, os,re;


class Reflect(object):

    def __init__(self):
        
        self.ami_id             = None;
        self.instnace_id        = None;
        self.instance_type      = None;
        self.public_hostname    = None;
        self.availability_zone  = None;
        self.current_spot_price = None;

        # make sure we're ec2 instance
        if not self.is_ec2(): return;
        
        # ok, so now populate all the fields
        self.instance_type      = self.__process_request('instance-type'              );
        self.instnace_id        = self.__process_request('instance-id'                );
        self.ami_id             = self.__process_request('ami-id'                     );
        self.availability_zone  = self.__process_request('placement/availability-zone'); 
        self.public_hostname    = self.__process_request('public-hostname'            );
        
        # now use this data to calculate the current price
        self.current_spot_price = self.__get_current_spot_price(                      \
                                                                self.instance_type,   \
                                                                self.availability_zone\
                                                               );
        
        
    def __process_request(self,rid):
        r = subprocess.Popen(['curl','-s',URL+rid],stdout=subprocess.PIPE).communicate()[0];
        return r;
        
        
    def is_ec2(self):
        return 'amzn' in os.uname()[2];
        
        
    def __get_current_spot_price(self, instanceType,availabilityZone):
        
        # create iso datetime string
        start_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z");
        
        # create connection to ec2
        conn = boto.connect_ec2();
        
        # get the current price
        prices = conn.get_spot_price_history(                                   \
                                             instance_type=instanceType        ,\
                                             start_time=start_time             ,\
                                             availability_zone=availabilityZone,\
                                             product_description='Linux/UNIX'   \
         
                                            )
        
        # make sure that we have at least 1 price to return 
        if len(prices) == 0:
            return None;
        else:
            try:
                return float(prices[0].price);
            except:
                return None;
        
        
def main():
    
    r = Reflect();
    print r.instance_type
    print r.instnace_id
    print r.availability_zone;
    print r.public_hostname;
    print r.current_spot_price;
    
if __name__ == '__main__':
    main()
        
    