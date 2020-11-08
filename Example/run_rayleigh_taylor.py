import subprocess as sp
import csv
import os
import sys

n_slave_nodes = int(sys.argv[1])
n_nodes = n_slave_nodes + 1

# Import master node attributes
master_node = {}
with open('./tmp/master_node.csv') as csvfile:
    master_node_reader = csv.reader(csvfile, delimiter='\t')
    for line in master_node_reader:
        master_node[line[0]] = line[1]

f = open("./generated_scripts/aws-run-rt.sh", "w")
f.write('#!/bin/sh' + '\n')
f.write("ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new ec2-user@" + master_node['public_ip']
        + " << EOF \n")
f.write('cd /home/ec2-user/data/IAMR/Exec/run2d' + '\n')
f.write('mpirun -np ' + str(n_nodes) + ' --hostfile hostfile ./amr2d.gnu.MPI.ex inputs.2d.rt |& tee aws-rayleigh-taylor.out' + '\n')
f.write("EOF")
f.close()

os.chmod('./generated_scripts/aws-run-rt.sh', 0o755)
sp.call(["./generated_scripts/aws-run-rt.sh"])

f = open("./generated_scripts/aws-transfer-rt.sh", "w")
f.write('#!/bin/sh' + '\n')
f.write('mkdir ./Example/aws-results' + '\n')
f.write('rsync -avhe "ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new" ec2-user@' + master_node['public_ip']
        + ':/home/ec2-user/data/IAMR/Exec/run2d/plt* ./Example/aws-results' + '\n')
f.write('rsync -avhe "ssh -i ec2-keypair.pem -o StrictHostKeyChecking=accept-new" ec2-user@' + master_node['public_ip']
        + ':/home/ec2-user/data/IAMR/Exec/run2d/aws-rayleigh-taylor.out ./Example/aws-results' + '\n')
f.close()

os.chmod('./generated_scripts/aws-transfer-rt.sh', 0o755)
sp.call(["./generated_scripts/aws-transfer-rt.sh"])
