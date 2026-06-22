#!/bin/csh
#gen_pbs version: 2.3.0
#PBS -A           PROJECT_NAME
#PBS -N           1_SSB_c1
#PBS -joe
#PBS -e           gsubmit.oe
#PBS -o           gsubmit.oe
#PBS -M           email
#PBS -mbe
#PBS -l           walltime=23:59:00
#PBS -l           select=1:ncpus=92:mpiprocs=92
#PBS -q           standard
#PBS -l           application=gaussian

# set up
 
 

### Set up scratch dir named by $PBS_JOBID
setenv GAUSS_SCRDIR $WORKDIR/tmp/$PBS_JOBID
if !(-e $GAUSS_SCRDIR) then
	 mkdir $GAUSS_SCRDIR
endif


### Go to the sub. directory
cd "$PBS_O_WORKDIR"

### Copy original input file because the executable may edit it.
cp $PBS_JOBNAME.com input.com
set INPUT="input.com"
set OUTPUT="$PBS_JOBNAME.log"



 
 



echo "Job $PBS_JOBID started on `date` ">JOB_${PBS_JOBID}_run.log

g16 $INPUT $OUTPUT SMP

echo "Job ended on `date`">>JOB_${PBS_JOBID}_run.log
