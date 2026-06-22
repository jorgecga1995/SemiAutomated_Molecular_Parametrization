#!/bin/bash
#=========================================================================================
# --- PBS Directives ---
#=========================================================================================
#gen_pbs version: 2.3.0
#PBS -A           PROJECT_NAME
#PBS -N           40_rdkit
#PBS -joe
#PBS -e           rdkit.oe
#PBS -o           rdkit.oe
#PBS -M           email
#PBS -mbe
#PBS -l           walltime=03:58:00
#PBS -l           select=1:ncpus=92:mpiprocs=2
#PBS -q           standard
#=========================================================================================
# --- Job Environment Setup ---
#=========================================================================================
echo "Job started on $(hostname) at $(date)"
echo "Job ID: $PBS_JOBID"
echo "Submission directory: $PBS_O_WORKDIR"

export SUBMIT_DIR="$PBS_O_WORKDIR"                 # Directory where you run 'qsub'
export SCRATCH_BASE="$WORKDIR/tmp"                 # Base directory for scratch space
export JOB_SCRATCH_DIR="$SCRATCH_BASE/$PBS_JOBID"  # Create a unique directory for this job on the scratch filesystem

# --- Define Input Files ---
export PYTHON_SCRIPT="conformer_search.py"
 

#=========================================================================================
# --- Execution Workflow ---
#=========================================================================================
echo "Creating scratch directory: $JOB_SCRATCH_DIR"
mkdir -p "$JOB_SCRATCH_DIR"
echo "Copying input files to scratch..."
cp "$SUBMIT_DIR/$PYTHON_SCRIPT" "$JOB_SCRATCH_DIR/"
 

echo "Changing to scratch directory..."
cd "$JOB_SCRATCH_DIR"
echo "Current working directory: $(pwd)"

# 4. Load modules and activate the conda environment
 
 
 
 
conda activate rdkit_env

echo "Starting RDKit Python script..."
time python "$PYTHON_SCRIPT"

EXIT_STATUS=$?   # Capture the exit code of the python script

echo "Copying output files back to $SUBMIT_DIR ..."
cp -rp . "$SUBMIT_DIR/"

echo "Deactivating conda environment..."
conda deactivate

echo "Cleaning up scratch directory..."
rm -rf "$JOB_SCRATCH_DIR"

echo "Job finished at $(date)"
echo "Exit status: $EXIT_STATUS"

exit $EXIT_STATUS   # Exit with the same status as the python script. If it failed, the job will be marked as Failed.


