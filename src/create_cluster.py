import subprocess as sp
import boto3 as boto
import os
import sys
import csv

# Use the updated image of the master node now to spawn "n_slave_nodes" slave instances.
ec2 = boto.resource('ec2')
master_node = {}
with open('./tmp/master_node.csv') as csvfile:
    master_node_reader = csv.reader(csvfile, delimiter='\t')
    for line in master_node_reader:
        master_node[line[0]] = line[1]

imageid_file = open('./tmp/image_id.txt', 'r')
image_id = str(imageid_file.read())

n_slave_nodes = int(sys.argv[1])

new_instances = ec2.create_instances(
    ImageId=image_id,
    InstanceType='t2.micro',
    MaxCount=n_slave_nodes,
    MinCount=n_slave_nodes,
    KeyName='ec2-keypair',
    SecurityGroupIds=[master_node['group_id']]
)

# Store slave node private IDs for /etc/hosts and create corresponding hostfile for mpirun.
private_ip_file = open("./tmp/private_ip.txt", "w")

hostfile_id = open("./tmp/hostfile", "w")
hostfile_id.write('localhost' + '\n')
k = 1
for instance in new_instances:
    instance.wait_until_running()
    instance.reload()
    private_ip_file.write(instance.private_ip_address + '\t node' + str(k) + '\n')
    hostfile_id.write('node' + str(k) + '\n')
    k += 1
private_ip_file.close()
hostfile_id.close()

# Script to append slave node ip addresses to master node's /etc/hosts/
f = open("./generated_scripts/aws-add-hosts.sh", "w")
f.write('#!/bin/sh' + '\n')
f.write('rsync -avhe "ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new" ./tmp/{private_ip.txt,hostfile} ec2-user@' + master_node['public_ip'] + ':~/ \n')
f.write("ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new ec2-user@" + master_node['public_ip'] + " << EOF \n")
f.write("cd ~" + "\n")
f.write("sudo -i" + "\n")
f.write("cd /home/ec2-user/" + "\n")
f.write("cat private_ip.txt >> /etc/hosts" + "\n")
f.write("exit" + "\n")
f.write("EOF")
f.close()

os.chmod('./generated_scripts/aws-add-hosts.sh', 0o755)
sp.call(["./generated_scripts/aws-add-hosts.sh"])
