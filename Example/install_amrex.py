import subprocess as sp
import csv
import os

# Import master node attributes
master_node = {}
with open('./tmp/master_node.csv') as csvfile:
    master_node_reader = csv.reader(csvfile, delimiter='\t')
    for line in master_node_reader:
        master_node[line[0]] = line[1]

# Construct script to install amrex and IAMR on the shared NFS drive.
f = open("./generated_scripts/aws-install-amrex.sh", "w")
f.write('#!/bin/sh' + '\n')
# Transfer script to build AMREX (AMR Libraries) and IAMR (Incompressible Navier Stokes solver)
f.write('rsync -avhe "ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new" ./Example/install-amrex.sh ec2-user@' + master_node['public_ip'] + ':~/ \n')
f.write('rsync -avhe "ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new" ./Example/inputs.2d.rt ec2-user@' + master_node['public_ip'] + ':~/ \n')
f.write("ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new ec2-user@" + master_node['public_ip'] + " << EOF \n")
f.write('mv /home/ec2-user/install-amrex.sh /home/ec2-user/data' + '\n')
f.write('cd /home/ec2-user/data' + '\n')
f.write('bash install-amrex.sh' + '\n')
f.write('exit' + '\n')
f.write("EOF")
f.close()

os.chmod('./generated_scripts/aws-install-amrex.sh', 0o755)
sp.call(["./generated_scripts/aws-install-amrex.sh"])
