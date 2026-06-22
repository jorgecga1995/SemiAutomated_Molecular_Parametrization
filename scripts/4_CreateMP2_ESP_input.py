#!/usr/bin/env python3
import os
import glob
import re

# ==========================================
# 1. CONFIGURATION
MOLECULE_LIST_FILE = "MP2_ESP_calcToDo_Jun14_for15.txt"    # Filename for the list of molecules to process
#/p/work/jorgecga/Switches_Jun8_2026/SwitchesFor-aRuCl3/AfterMay8_2026/MP2_ESP_calcToDo_Jun14.txt
# ==========================================
# 2. TEMPLATE DEFINITIONS

COM_TEMPLATE = """%chk={job_name}_OpFr.chk
%nprocshared=92
%mem=350Gb
#p MaxDisk=1TB mp2/aug-cc-PVTZ pop=mk iop(6/33=2,6/41=10,6/42=17) scf=tight prop=FitCharge Geom=Checkpoint

MP2 ESP for {job_name}    

{charge}   {multiplicity}


"""
# basis_set = 6-311+G(2df,p) or 6-311+G(2df,p) if anion

SUB_TEMPLATE = """#!/bin/csh
#gen_pbs version: 2.3.0
#PBS -A           PROJECT_NAME
#PBS -N           {job_name}
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

echo "Job $PBS_JOBID started on `date` ">JOB_${{PBS_JOBID}}_run.log
g16 $INPUT $OUTPUT SMP
echo "Job ended on `date`">>JOB_${{PBS_JOBID}}_run.log
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

        if not conformers:
            print(f"Processing Molecule {mol_id} inside '{mol_dir_path}'... No conformers listed to generate.")
            continue
            
        print(f"Processing Molecule {mol_id} inside '{mol_dir_path}' with {len(conformers)} conformer(s)...")

        for conf in conformers:
            # 1. Read coordinates from target XYZ File
            # xyz_path = os.path.join(
            #     mol_dir_path, 
            #     "0_ConformerSearch", 
            #     "unique_conformers_xyz", 
            #     f"unique_conformer_{conf}.xyz"
            # )
            
            # if not os.path.exists(xyz_path):
            #     print(f"  ❌ XYZ file not found: {xyz_path}")
            #     continue
                
            # with open(xyz_path, "r") as f:
            #     xyz_lines = f.readlines()
            
            # # XYZ files have atom count (line 1), comment (line 2), and coords (line 3+)
            # if len(xyz_lines) > 2:
            #     coords = "".join(xyz_lines[2:])
            # else:
            #     print(f"  ❌ File structure error in {xyz_path}")
            #     continue
            
            # 2. Setup output directories
            #/20_29/24_S01/3_Parametrization/Gauss-Ante/conformer0/24_S01_c0.com
            target_out_dir = os.path.join(
                mol_dir_path,
                "3_Parametrization",
                "Gauss-Ante",
                f"conformer{conf}"
            )
            os.makedirs(target_out_dir, exist_ok=True)
# The code above is awesome:
#Scenario A: The directory already fully exists  -> bc exist_ok=True is set, it does nothing and moves to the next line of code without error.
#Scenario B: The directory does not exist at all	Python will create all the nested folders in the path from scratch 
#Scenario C: Only a part of the path exists     	Python detects which parts of the path are already present and only creates the missing subdirectories
       
            # Names of output files
            job_name = f"{mol_folder_name}_c{conf}"
            com_filename = os.path.join(target_out_dir, f"{job_name}.com")
            sub_filename = os.path.join(target_out_dir, "gaussSub.sh")
            
            # 3. Generate and Write Gaussian (.com) file
            #basis_set = "6-311G(2df,p)" if int(charge) >= 0 else "6-311+G(2df,p)"
                 
            com_content = COM_TEMPLATE.format(
                job_name=job_name,
                #basis_set=basis_set,
                charge=charge,
                multiplicity="1"
            )
            with open(com_filename, "w") as f:
                f.write(com_content)
                
            # 4. Generate and Write Submit script (gaussSub.sh)
            sub_content = SUB_TEMPLATE.format(job_name=job_name)
            with open(sub_filename, "w") as f:
                f.write(sub_content)
                
            # Make submission script executable
            os.chmod(sub_filename, 0o755)
            
    print("\n✅ Automation completed successfully!")

if __name__ == "__main__":
    run_automation()