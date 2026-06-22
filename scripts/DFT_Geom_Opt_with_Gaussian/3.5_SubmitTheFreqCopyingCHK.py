#!/usr/bin/env python3
import os
import glob
import re
import subprocess
import shutil

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Filename for the list of molecules to process
MOLECULE_LIST_FILE = "ToCheckFreqWTerGrid.txt"

# ==========================================
# 2. PARSE INPUT DATA FROM FILE
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
        charge = lines[1].split()[1]
        
        # Conformers start from the 3rd line. Filter out any 'no' entries.
        conformers = [c for c in lines[2:] if 'no' not in c and c]

        molecules.append((mol_id, charge, conformers))
        
    return molecules


# ==========================================
# 3. JOB SUBMISSION ENGINE
# ==========================================
def submit_jobs():
    """Main function to cycle through folders and submit jobs."""
    molecules = parse_molecule_list_from_file(MOLECULE_LIST_FILE)
    
    if not molecules:
        print("No molecules found to submit. Exiting.")
        return
        
    print(f"Parsed {len(molecules)} molecule entries from '{MOLECULE_LIST_FILE}'. Starting submission...\n")
    
    submitted_count = 0
    missing_count = 0

    for mol_id, _, conformers in molecules:
        # Determine first layer folder range (e.g., '20_29' if mol_id is 24)
        try:
            val = int(mol_id)
            lower_bound = (val // 10) * 10
            upper_bound = lower_bound + 9
            first_layer_glob = f"{lower_bound}_{upper_bound}"
        except ValueError:
            continue

        # Locate the molecule directory
        mol_path_pattern = os.path.join(".", first_layer_glob, f"{mol_id}_*")
        matching_dirs = glob.glob(mol_path_pattern)
        
        if not matching_dirs:
            print(f"⚠️ Molecule {mol_id}: Directory not found ({mol_path_pattern}). Skipping.")
            continue
            
        mol_dir_path = matching_dirs[0]
        mol_folder_name = os.path.basename(mol_dir_path) # e.g. "25_S01"

        for conf in conformers:
            job_name = f"{mol_folder_name}_c{conf}"
            # Target directory containing the submission script
            target_dir = os.path.join(
                mol_dir_path,
                "1_DFT_opt",
                f"conformer{conf}",
                "Gauss",
                "SuperFineGrid_FreqTest"
            )
            sub_script_path = os.path.join(target_dir, "gaussSub.sh")

            # Copy checkpoint file from previous calc
            chk_file = os.path.join(mol_dir_path, "1_DFT_opt", f"conformer{conf}", "Gauss", f"{job_name}_OpFr.chk")
            shutil.copy(chk_file, target_dir)
            chk_file_copy = os.path.join(target_dir, f"{job_name}_OpFr.chk")

            # Verify the submission script and the chk file copy exist before trying to run qsub
            if not os.path.exists(sub_script_path):
                print(f"❌ Conformer {conf} of Molecule {mol_id}: Submission script not found at {sub_script_path}")
                missing_count += 1
                continue
            
            if not os.path.exists(chk_file_copy):
                print(f"❌ Conformer {conf} of Molecule {mol_id}: chk file not found at {target_dir}")
                missing_count += 1
                continue

            print(f"🚀 Submitting: Molecule {mol_id}, Conformer {conf}...")
            
            try:
                # Run qsub. cwd=target_dir executes the command *inside* that directory
                # so that PBS correctly captures PBS_O_WORKDIR.
                result = subprocess.run(       # function that spawns a new process, waits for it to finish, and then returns a CompletedProcess instance.
                    ["qsub", "gaussSub.sh"], 
                    cwd=target_dir,            # Current Working Directory. Temporarily changes Python's working directory only for this specific execution.
                    stdout=subprocess.PIPE,    # Redirects standard output (the normal message returned by a command) to a buffer.
                    stderr=subprocess.PIPE,    # Redirects standard error (error messages) to a buffer.
                    text=True,                 # Tells Python to return the output as a normal text string rather than raw bytes.
                    check=True                 # Tells Python to automatically raise an error if the command fails (exits with a non-zero status).
                )
                
                # Output the Job ID returned by qsub
                job_id = result.stdout.strip()
                print(f"   ↳ Success! Job ID: {job_id}")
                submitted_count += 1

            except subprocess.CalledProcessError as e:
                print(f"   ❌ Error submitting job: {e.stderr.strip()}")
                missing_count += 1
            except Exception as e:
                print(f"   ❌ Execution failed: {str(e)}")
                missing_count += 1

    # --- Print Summary ---
    print("\n" + "="*40)
    print("Submission Summary:")
    print(f"  Total Jobs Successfully Submitted: {submitted_count}")
    print(f"  Failed/Missing Jobs:               {missing_count}")
    print("="*40)

if __name__ == "__main__":
    submit_jobs()