#!/bin/sh

aws_home=../

FILE1=./aws-results
if [ -f "$FILE1" ]; then
    rm -rf aws-results
fi

FILE2=$aws_home/generated_scripts
if [ ! -d "$FILE2" ]; then
    mkdir $aws_home/generated_scripts
fi

FILE3=$aws_home/tmp
if [ ! -d "$FILE3" ]; then
    mkdir $aws_home/tmp
fi

echo "For the Rayleigh-Taylor example:"
echo "	please use 1 slave-node (Domain decomposed in two sub-domains)"

read -p 'number of slave nodes: ' n_slave_nodes
read -p 'mount volume size (in GiB): ' vol_size

cd $aws_home

echo "1) creating default (master) instance to be replicated"
python3 ./src/create_default_instance.py
echo "2) copying Linux image with updated libraries for replication"
python3 ./src/create_image.py
echo "3) spinning up " $n_slave_nodes " replica (slave) instances"
python3 ./src/create_cluster.py $n_slave_nodes
echo "4) creating and attaching a shared nfs-volume of size " $vol_size " GiB"
python3 ./src/create_volume.py $vol_size
echo "5) installing a parallel, adaptive mesh refinement (AMR) variable-density incompressible Navier-Stokes code to solve the Rayleigh Taylor problem"
python3 ./Example/install_amrex.py
echo "6) run Rayleigh Taylor problem"
python3 ./Example/run_rayleigh_taylor.py $n_slave_nodes
echo "7) kill instances, unmount volumes and delete security group and key-pair"
python3 ./src/kill_instance.py

