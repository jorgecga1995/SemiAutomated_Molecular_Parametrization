#!/usr/bin/env python3
import os
import glob
import re

# ==========================================
# 1. CONFIGURATION
MOLECULE_LIST_FILE = "MP2_ESP_calcToDo_Jun14.txt"    # Filename for the list of molecules to process
# ==========================================
# 2. TEMPLATE DEFINITIONS

SUB_TEMPLATE = """#!/bin/bash
#gen_pbs version: 2.3.0
#PBS -l select=1:ncpus=92:mpiprocs=1
#PBS -l walltime=00:59:00
#PBS -A           PROJECT_NAME
#PBS -e ante.err
#PBS -o ante.out
#PBS -q standard
#PBS -N {job_name}_ante_resp
#PBS -V
#PBS -M email
#PBS -mbe
#=========================================================================================
export JobFilename="{job_name}"
export Mol="{MOL}"
export charge="{charge}"
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

"""

# ==========================================
# 3. PARSE INPUT DATA FROM FILE
# ==========================================
def parse_molecule_list_from_file(filepath):
    """Parses molecule data from a file where molecules are separated by blank lines."""
    if not os.path.exists(filepath):
        print(f"❌ Error: The input file '{filepath}' was not found.")
        return []

    with open(filepath, 'r') as f:
        content = f.read()
    
    molecules = []
    # Split the file content into blocks using one or more newlines as a delimiter
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
            
        mol_id = lines[0]
        # The charge line is expected to be 'c <charge>'
        charge = lines[1].split()[1]
        
        # Conformers start from the 3rd line. Filter out any 'no' entries.
        conformers = [c for c in lines[2:] if 'no' not in c and c]

        molecules.append((mol_id, charge, conformers))
        
    return molecules

# ==========================================
# 4. DIRECTORY MATCHING & WRITING ENGINE
# ==========================================
def run_automation():
    """Main function to drive the automation process."""
    molecules = parse_molecule_list_from_file(MOLECULE_LIST_FILE)
    
    if not molecules:
        print("No molecules to process. Exiting.")
        return
        
    print(f"Parsed {len(molecules)} molecule entries from '{MOLECULE_LIST_FILE}'.")
    
    for mol_id, charge, conformers in molecules:
        # Determine first layer folder range (e.g., '20_29' if mol_id is 24)
        try:
            val = int(mol_id)
            lower_bound = (val // 10) * 10
            upper_bound = lower_bound + 9
            first_layer_glob = f"{lower_bound}_{upper_bound}"
        except ValueError:
            print(f"Skipping invalid Molecule ID format: {mol_id}")
            continue

        # Use glob to dynamically find the correct directory path structure
        # Matches e.g., "./20_29/25_S01" where S01 can be any alphanumeric suffix.
        mol_path_pattern = os.path.join(".", first_layer_glob, f"{mol_id}_*")
        matching_dirs = glob.glob(mol_path_pattern)
        
        if not matching_dirs:
            print(f"⚠️ Warning: Directory matching '{mol_path_pattern}' was not found. Skipping molecule {mol_id}.")
            continue
            
        mol_dir_path = matching_dirs[0] # Take first match
        mol_folder_name = os.path.basename(mol_dir_path) # e.g. "25_S01"
        MOL = mol_folder_name[-3:]

        if not conformers:
            print(f"Processing Molecule {mol_id} inside '{mol_dir_path}'... No conformers listed to generate.")
            continue
            
        print(f"Processing Molecule {mol_id} inside '{mol_dir_path}' with {len(conformers)} conformer(s)...")

        for conf in conformers:

            target_out_dir = os.path.join(
                mol_dir_path,
                "3_Parametrization",
                "Gauss-Ante",
                f"conformer{conf}"
            )
            os.makedirs(target_out_dir, exist_ok=True)
       
            # Names of output files
            job_name = f"{mol_folder_name}_c{conf}"
            sub_filename = os.path.join(target_out_dir, "1_AntechamberSub.sh")
            
            # 3. Generate and Write Gaussian (.com) file
                 
            # com_content = COM_TEMPLATE.format(
            #     job_name=job_name,
            #     #basis_set=basis_set,
            #     charge=charge,
            #     multiplicity="1"
            # )
            # with open(com_filename, "w") as f:
            #     f.write(com_content)
                
            # 4. Generate and Write Submit script (gaussSub.sh)
            sub_content = SUB_TEMPLATE.format(
                job_name=job_name,
                MOL=MOL,
                charge=charge)
            with open(sub_filename, "w") as f:
                f.write(sub_content)
                
            # Make submission script executable
            os.chmod(sub_filename, 0o755)
            
    print("\n✅ Automation completed successfully!")

if __name__ == "__main__":
    run_automation()