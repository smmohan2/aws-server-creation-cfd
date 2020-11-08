import boto3 as boto
import csv
from botocore.exceptions import ClientError

master_node = {}
with open('./tmp/master_node.csv') as csvfile:
    master_node_reader = csv.reader(csvfile, delimiter='\t')
    for line in master_node_reader:
        master_node[line[0]] = line[1]

resource = boto.resource('ec2')
client = boto.client('ec2')

demo_instances = resource.instances.filter(
    Filters=[{'Name': 'key-name', 'Values': ['ec2-keypair']}]
)

for instance in demo_instances:
    if instance.public_ip_address is not None:
        public_ip_add = instance.public_ip_address
        instance.terminate()
        instance.wait_until_terminated()

print("instance(s) deleted")

try:
    client.delete_security_group(GroupId=master_node['group_id'])
    print("security group deleted")
except ClientError as e:
    print("security group already deleted")

try:
    client.delete_key_pair(KeyName='ec2-keypair')
    print("key-pair deleted")
except ClientError as e:
    print("key-pair already deleted")

try:
    imageid_file = open('./tmp/image_id.txt', 'r')
    image_id = str(imageid_file.read())
    client.deregister_image(ImageId=image_id)
    print("Amazon Linux image deleted")
except ClientError as e:
    print("image already deleted")

try:
    vol_id_file = open('./tmp/vol_id.txt', 'r')
    vol_id = str(vol_id_file.read())
    client.delete_volume(VolumeId=vol_id)
    print("volume deleted")
except ClientError as e:
    print("volumes already deleted")
