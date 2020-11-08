import boto3 as boto
import os
import time
import csv

ec2 = boto.resource('ec2')

# Default Instance Attributes
default_instance_att = {}

# Creating Security Group
sec_group = ec2.create_security_group(
    GroupName='SG_RESCALE',
    Description='security group for rescale'
)
sec_group.authorize_ingress(
    CidrIp='0.0.0.0/0',
    IpProtocol='tcp',
    FromPort=0,
    ToPort=65535
)

default_instance_att['group_id'] = sec_group.id

# Create and store a key-pair for SSH
outfile = open('ec2-keypair.pem', 'w')
key_pair = ec2.create_key_pair(KeyName='ec2-keypair')
KeyPairOut = str(key_pair.key_material)
outfile.write(KeyPairOut)

os.chmod('ec2-keypair.pem', 0o600)

# create a new EC2 instance
instances = ec2.create_instances(
    ImageId='ami-00c03f7f7f2ec15c3',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    KeyName='ec2-keypair',
    SecurityGroupIds=[sec_group.id]
)

instances[0].wait_until_running()

running_instances = ec2.instances.filter(
    Filters=[{'Name': 'key-name', 'Values': ['ec2-keypair']}]
)
for instance in running_instances:
    if instance.public_ip_address is not None: # Ignores all terminated instances
        # Public IP of default instance
        public_ip_add = instance.public_ip_address
        # Get Zone
        zone_add = str(instance.placement['AvailabilityZone'])

        default_instance_att['zone_id'] = zone_add
        default_instance_att['instance_id'] = instance.id
        default_instance_att['public_ip'] = instance.public_ip_address
        default_instance_att['private_ip'] = instance.private_ip_address

# Store relevant master-node attributes
w = csv.writer(open("./tmp/master_node.csv", "w"), delimiter='\t')
for key, val in default_instance_att.items():
    w.writerow([key, val])

# Construct script to transfer/update the master-node before replica images are created.
f = open("./generated_scripts/aws-login-create-image.sh", "w")
f.write('#!/bin/sh' + '\n')
# Transfer AWS config and credential files
f.write('rsync -avhe "ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new" ~/.aws/credentials ec2-user@' + public_ip_add + ':~/ \n')
f.write('rsync -avhe "ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new" ~/.aws/config ec2-user@' + public_ip_add + ':~/ \n')
f.write("ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new ec2-user@" + public_ip_add + " << EOF \n")
# Update Libraries
f.write("echo 'yes' | sudo yum update" + "\n")
f.write("sudo yum -y install build-essential" + "\n")
f.write("sudo yum -y install openmpi-devel" + "\n")
f.write("sudo yum -y install blas" + "\n")
f.write("sudo yum -y install git" + "\n")
f.write("sudo yum -y install gcc-c++" + "\n")
f.write('sudo yum -y group install "Development Tools"' + "\n")
# Add path to OPENMPI compilers
f.write('echo "export PATH=/usr/lib64/openmpi/bin:$PATH" >> /home/ec2-user/.bashrc' + "\n")
f.write('echo "export LD_LIBRARY_PATH=/usr/lib64/openmpi/lib" >> /home/ec2-user/.bashrc' + "\n")
f.write("cd ~" + "\n")
# Generate SSH key and store in authorised keys.
f.write('ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa' + "\n")
f.write("cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys" + "\n")
# Store AWS credentials in ~/.aws/
f.write("mkdir ~/.aws/" + "\n")
f.write("mv credentials config ~/.aws/" + "\n")
f.write("exit" + "\n")
f.write("EOF")
f.close()

# https://stackoverflow.com/questions/6025546/issues-trying-to-ssh-into-a-fresh-ec2-instance-with-paramiko
# Adding a pause to ensure instance is ready before SSH
time.sleep(45)
