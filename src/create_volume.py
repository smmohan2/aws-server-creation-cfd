import subprocess as sp
import boto3 as boto
import csv
import os
import time
import sys

client = boto.client('ec2')

# Create a NFS volume, attach it to the master instance and mount it on all slave nodes.

# Import master node attributes
master_node = {}
with open('./tmp/master_node.csv') as csvfile:
    master_node_reader = csv.reader(csvfile, delimiter='\t')
    for line in master_node_reader:
        master_node[line[0]] = line[1]

# Size in GiB of volume to be created.
volume_size = int(sys.argv[1])

private_slave_ips = []
private_slave_names = []
with open('./tmp/private_ip.txt') as csvfile:
    private_id_reader = csv.reader(csvfile, delimiter='\t')
    for line in private_id_reader:
        private_slave_ips.append(line[0])
        private_slave_names.append(line[1])

client = boto.client('ec2')

# response = client.create_volume(AvailabilityZone=zone_id, Size=2)
response = client.create_volume(AvailabilityZone=master_node['zone_id'], Size=volume_size)
vol_id = str(response['VolumeId'])

vol_id_file = open('./tmp/vol_id.txt', 'w')
vol_id_file.write(vol_id)
vol_id_file.close()

client.get_waiter('volume_available').wait(VolumeIds=[vol_id])

ec2_resource = boto.resource('ec2')
demo_instances = ec2_resource.instances.filter(
    Filters=[{'Name': 'key-name', 'Values': ['ec2-keypair']}]
)
for instance in demo_instances:
    if instance.id == master_node['instance_id']:  # Iterate through non-terminated instances in AWS
        instance.attach_volume(Device='/dev/sdf', InstanceId=master_node['instance_id'], VolumeId=vol_id)
        break

time.sleep(30)

# Local Script to run from Master node to mount
g = open("./generated_scripts/aws-mount-volume-on-slave.sh", "w")
g.write('#!/bin/sh' + '\n')
g.write('echo "Mounting on node" $HOSTNAME' + '\n')
g.write('mkdir /home/ec2-user/data' + '\n')
g.write('sudo mount ' + master_node['private_ip'] + ':/home/ec2-user/data /home/ec2-user/data' + '\n') 
g.close()

# Local Script to run from Master node to mount
temp = ''.join(private_slave_names)
h = open("./generated_scripts/aws-mount-across-nodes.sh", "w")
h.write('#!/bin/sh' + '\n')
h.write('for node_id in' + temp + '\n')
h.write('do'+ '\n')
h.write("\t ssh -o \"StrictHostKeyChecking no\" ${node_id} \'bash -s\' < /home/ec2-user/aws-mount-volume-on-slave.sh" + '\n')
h.write('done' + '\n')
h.close()

# Script to mount NFS volume on all slave nodes.
f = open("./generated_scripts/aws-create-volume.sh", "w")
f.write('#!/bin/sh' + '\n')
f.write('rsync -avhe "ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new" ./generated_scripts/aws-mount-volume-on-slave.sh ec2-user@' + master_node['public_ip'] + ':~/ \n')
f.write('rsync -avhe "ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new" ./generated_scripts/aws-mount-across-nodes.sh ec2-user@' + master_node['public_ip'] + ':~/ \n')
f.write("ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new ec2-user@" + master_node['public_ip'] + " << EOF \n")
f.write('sudo mkfs.ext4 /dev/xvdf' + '\n')
# Creating a mountpoint
f.write('mkdir /home/ec2-user/data' + '\n')
f.write('sudo mount /dev/xvdf /home/ec2-user/data' + '\n')
# Change permission so ec2-user has privileges.
f.write('sudo chown -R ec2-user data' + '\n')
f.write('cd ~' + '\n')
f.write('sudo -i' + '\n')
f.write('cd /home/ec2-user/' + '\n')
f.write('echo "/home/ec2-user/data (rw)" >> /etc/exports' + '\n')
f.write('exit' + '\n')
f.write('cd ~' + '\n')
f.write('sudo /sbin/service rpcbind start' + '\n')
f.write('sudo /sbin/service nfs start' + '\n')
# mount on each 'slave' node by executing script created above:
f.write('bash aws-mount-across-nodes.sh' + '\n')
f.write("EOF")
f.close()

os.chmod('./generated_scripts/aws-create-volume.sh', 0o755)
sp.call(["./generated_scripts/aws-create-volume.sh"])
