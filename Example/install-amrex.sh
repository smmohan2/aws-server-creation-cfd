#!/bin/sh
git clone https://github.com/AMReX-Codes/amrex.git
git clone https://github.com/AMReX-Codes/IAMR.git
export AMREX_HOME=/home/ec2-user/data/amrex
cd IAMR/Exec/run2d
mv /home/ec2-user/{hostfile,inputs.2d.rt} ./
make realclean
make