#!/bin/bash
#=========================================================================================
# --- PBS Directives ---
#=========================================================================================
#gen_pbs version: 2.3.0
#PBS -A           PROJECT_NAME
#PBS -N           3_c0_b97-3c_OpFr
#PBS -joe
#PBS -e           0.9_DFT_OpFr_c0.oe
#PBS -o           0.9_DFT_OpFr_c0.oe
#PBS -M           email
#PBS -mbe
#PBS -l           walltime=23:59:00
#PBS -l           select=1:ncpus=92:mpiprocs=92
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
export PYTHON_SCRIPT="0.9_b97-3c_OptFreq.py"
 

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
 
 
 
 
conda activate psi4_env

echo "Starting Psi4 Python script..."
time python "$PYTHON_SCRIPT"

EXIT_STATUS=$?   # Capture the exit code of the python script

echo "Copying output files back to $SUBMIT_DIR ..."
cp -p *.dat "$SUBMIT_DIR/" || true        # 'cp -p' preserve timestamps.
cp -p *.xyz "$SUBMIT_DIR/" || true        # `|| true` prevents the script from failing if a file doesn't exist
cp -p *.log "$SUBMIT_DIR/" || true
cp -p *.txt "$SUBMIT_DIR/" || true

echo "Deactivating conda environment..."
conda deactivate

echo "Cleaning up scratch directory..."
rm -rf "$JOB_SCRATCH_DIR"

echo "Job finished at $(date)"
echo "Exit status: $EXIT_STATUS"

exit $EXIT_STATUS   # Exit with the same status as the python script. If it failed, the job will be marked as Failed.


