#!/usr/bin/env python3
import os
import glob
import re

# ==========================================
# 1. CONFIGURATION
# ==========================================
MOLECULE_LIST_FILE = "Opt_wCharges_done.txt"

# ==========================================
# 2. PARSE INPUT DATA FROM FILE
# ==========================================
def parse_molecule_list_from_file(filepath):
    if not os.path.exists(filepath):
        print(f"❌ Error: The input file '{filepath}' was not found.")
        return []

    with open(filepath, 'r') as f:
        content = f.read()
    
    molecules = []
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
            
        mol_id = lines[0]
        charge = lines[1].split()[1]
        conformers = [c for c in lines[2:] if 'no' not in c and c]
        molecules.append((mol_id, charge, conformers))
        
    return molecules

# ==========================================
# 3. LOG PARSING ENGINE
# ==========================================
def get_first_frequency(log_path):
    """
    Reads the log file line by line to find the first frequency.
    Returns the float value, or a string indicating the error/status.
    """
    if not os.path.exists(log_path):
        return "File Missing"
    
    try:
        with open(log_path, 'r') as f:
            for line in f:
                if "Frequencies --" in line:
                    # Example line: " Frequencies --    25.4868               58.0783               61.5810"
                    # split() breaks it into: ['Frequencies', '--', '25.4868', '58.0783', '61.5810']
                    tokens = line.split()
                    if len(tokens) >= 3:
                        try:
                            # The first frequency is always the 3rd item (index 2)
                            first_freq = float(tokens[2])
                            return first_freq
                        except ValueError:
                            return "Parse Error"
        # If the loop finishes without finding the string, the job likely crashed or hasn't reached freq yet
        return "Incomplete / Not Reached"
    except Exception as e:
        return f"Read Error: {str(e)}"

# ==========================================
# 4. MAIN EXECUTION
# ==========================================
def check_logs():
    molecules = parse_molecule_list_from_file(MOLECULE_LIST_FILE)
    
    if not molecules:
        print("No molecules found to process. Exiting.")
        return
        
    print(f"Scanning Gaussian log files based on '{MOLECULE_LIST_FILE}'...\n")
    
    # Header for our report
    print(f"{'Molecule':<10} | {'Conformer':<10} | {'Status':<25} | {'1st Frequency (cm^-1)':<20}")
    print("-" * 75)

    for mol_id, _, conformers in molecules:
        try:
            val = int(mol_id)
            lower_bound = (val // 10) * 10
            upper_bound = lower_bound + 9
            first_layer_glob = f"{lower_bound}_{upper_bound}"
        except ValueError:
            continue

        mol_path_pattern = os.path.join(".", first_layer_glob, f"{mol_id}_*")
        matching_dirs = glob.glob(mol_path_pattern)
        
        if not matching_dirs:
            continue
            
        mol_dir_path = matching_dirs[0]
        mol_folder_name = os.path.basename(mol_dir_path)

        for conf in conformers:
            job_name = f"{mol_folder_name}_c{conf}"
            log_path = os.path.join(
                mol_dir_path,
                "1_DFT_opt",
                f"conformer{conf}",
                "Gauss",
                f"{job_name}.log"
            )

            # Extract the frequency
            freq_result = get_first_frequency(log_path)

            # Determine the status
            if isinstance(freq_result, float):
                if freq_result < 0:
                    status = "❌ Imaginary (Saddle)"
                    freq_str = f"{freq_result:.4f}"
                else:
                    status = "✅ True Minimum"
                    freq_str = f"{freq_result:.4f}"
            else:
                status = f"⚠️ {freq_result}"
                freq_str = "N/A"

            # Print formatted row
            print(f"{mol_id:<10} | {conf:<10} | {status:<25} | {freq_str:<20}")

    print("-" * 75)
    print("\nLog check complete.")

if __name__ == "__main__":
    check_logs()