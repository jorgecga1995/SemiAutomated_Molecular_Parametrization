#!/bin/bash
#gen_pbs version: 2.3.0
#PBS -l select=1:ncpus=92:mpiprocs=1
#PBS -l walltime=00:59:00
#PBS -A           PROJECT_NAME
#PBS -e ante.err
#PBS -o ante.out
#PBS -q standard
#PBS -N 41_S18_c0_ante_resp
#PBS -V
#PBS -M email
#PBS -mbe
#=========================================================================================
export JobFilename="41_S18_c0"
export Mol="S18"
export charge="0"
export multiplicity="1"
export Gaussian_Log_File="$JobFilename.log"
#=========================================================================================
export SUBMIT_DIR="$PBS_O_WORKDIR"                 # Directory where you run 'qsub'
export SCRATCH_BASE="$WORKDIR/tmp"                 # Base directory for scratch space
export JOB_SCRATCH_DIR="$SCRATCH_BASE/$PBS_JOBID"  # Create a unique directory for this job on the scratch filesystem
echo "Job started on $(hostname) at $(date)"
echo "Job ID: $PBS_JOBID"
echo "Submission directory: $PBS_O_WORKDIR"
#=========================================================================================

echo "Creating scratch directory: $JOB_SCRATCH_DIR"
mkdir -p "$JOB_SCRATCH_DIR"
echo "Copying input files to scratch..."
cp "$SUBMIT_DIR/$Gaussian_Log_File" "$JOB_SCRATCH_DIR/"

echo "Changing to scratch directory..."
cd "$JOB_SCRATCH_DIR"
echo "Current working directory: $(pwd)"

# 4. Load modules and activate conda environment (as needed)
module purge
module load gcc/12.2.1
module load nvidia/cuda/cuda-12.4
module load openmpi/5.0.7

source amber.sh

#=========================================================================================
antechamber -i $JobFilename.log -fi gout -o $Mol.prepi -fo prepi -c resp -nc $charge -m $multiplicity -rn $Mol
cp NEWPDB.PDB $Mol.pdb
parmchk2 -i $Mol.prepi -f prepi -o $Mol.frcmod -a Y


EXIT_STATUS=$?   # Capture the exit code
#=========================================================================================

echo "Copying output files back to $SUBMIT_DIR ..."
cp -rp . "$SUBMIT_DIR/"    

echo "Cleaning up scratch directory..."
rm -rf "$JOB_SCRATCH_DIR"

echo "Job finished at $(date)"
echo "Exit status: $EXIT_STATUS"

exit $EXIT_STATUS   # Exit with the same status as antechamber. If it failed, the job will be marked as Failed.

