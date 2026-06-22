import sys
import os
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.EnumerateStereoisomers import EnumerateStereoisomers, StereoEnumerationOptions
from rdkit.Chem import rdMolDescriptors

sys.path.append(os.path.join(os.environ['CONDA_PREFIX'],'share','RDKit','Contrib'))
from SA_Score import sascorer

import numpy as np

# --- New Function to Calculate Boltzmann Probabilities ---
def calculate_boltzmann_probabilities(energies, temperature_K):
    """
    Calculates the Boltzmann probability of each conformer at a given temperature.

    Args:
        energies (list or np.array): A list of conformer energies in kcal/mol.
        temperature_K (float): The temperature in Kelvin.

    Returns:
        np.array: An array of Boltzmann probabilities for each conformer.
    """
    # Using the gas constant R in kcal/(mol·K)
    GAS_CONSTANT = 0.001987204
    
    if temperature_K <= 0:
        # At T=0, only the lowest energy state is populated.
        probabilities = np.zeros(len(energies))
        probabilities[np.argmin(energies)] = 1.0
        return probabilities

    energies = np.array(energies)
    
    # Shift energies to prevent numerical overflow with np.exp()
    # This does not change the final probabilities.
    relative_energies = energies - np.min(energies)
    
    # Calculate the exponent term for each conformer
    exp_terms = np.exp(-relative_energies / (GAS_CONSTANT * temperature_K))
    
    # Calculate the partition function Q
    partition_function = np.sum(exp_terms)
    
    # Calculate and return the probabilities
    probabilities = exp_terms / partition_function
    
    return probabilities

# --- 1. Read the Molecule from a File ---
input_file = '/p/home/jorgecga/SwitchesFor-aRuCl3/AfterMay8_2026/0_9/5_HAP/HAP.mol' # Or 'pyri.pdb', etc.
mol = Chem.MolFromMolFile(input_file, removeHs=False)
# mol = Chem.MolFromMol2File(input_file, removeHs=False)


if mol is None:
    raise ValueError("\n Molecule could not be read from the file.")
if mol:
    charge = Chem.GetFormalCharge(mol)
    print(f"\nMolecule was read successfully!")
    print(f"RDKit interpreted the overall charge as: {charge}")

num_rot_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
print(f"Number of rotatable bonds in the molecule: {num_rot_bonds}")

# --- SA_score? ---

Synthetic = sascorer.calculateScore(mol)
print(f"SA_score: {Synthetic}")



# --- 2.0 Isomer Generation ---

print("Generating isomers...")
# Force generation of all stereoisomers (e.g., E/Z)
opts = StereoEnumerationOptions(onlyUnassigned=False)
isomers = list(EnumerateStereoisomers(mol, options=opts))
print(f"Generated {len(isomers)} stereoisomers.")

# --- 2.1 Conformer Generation ---
num_conf_per_isomer = 10
if num_rot_bonds == 1:
    num_conf_per_isomer = 3
elif num_rot_bonds == 2:
    num_conf_per_isomer = 9
elif num_rot_bonds == 3:
    num_conf_per_isomer = 27
elif num_rot_bonds >= 4:
    num_conf_per_isomer = 81


print("Generating conformers for all isomers...")
mol.RemoveAllConformers() # Clear any existing conformers in the base mol object

all_cids = []
# Loop through each generated isomer
for iso in isomers:
    print(f"Isomer (SMILES: {Chem.MolToSmiles(iso)}) generated, looking at conformers ...")
    Synthetic = sascorer.calculateScore(iso)
    print(f"Isomer SA_score: {Synthetic}")
    # Generate x conformers for this specific isomer geometry
    iso_cids = AllChem.EmbedMultipleConfs(iso, numConfs=num_conf_per_isomer, params=AllChem.ETKDGv2())

    # Transfer the resulting 3D conformers back to the main 'mol' object
    for cid in iso_cids:
        conf = iso.GetConformer(cid)
        # AddConformer returns the new unique integer ID assigned in the main mol
        new_cid = mol.AddConformer(conf, assignId=True)
        all_cids.append(new_cid)

# Reassign to 'cids' so the downstream code works seamlessly
cids = all_cids
print(f"Generated a total of {len(cids)} conformers across all isomers.")

print("Optimizing conformers with MMFF94...")
# This will optimize all conformers (both E and Z geometries) loaded into 'mol'
results = AllChem.MMFFOptimizeMoleculeConfs(mol)
print("Optimization complete.")



# 2.2 --- Sort and Print Energies ---------------------------------
conformer_energies = []
for i, res in enumerate(results):
    energy = res[1]
    conformer_id = i
    conformer_energies.append((energy, conformer_id))
conformer_energies.sort()

print("\nConformers Sorted by Energy (Lowest to Highest):")
print("-" * 50)
print(f"{'Rank':<10} {'Conformer ID':<15} {'Energy (kcal/mol)':<25}")
print("-" * 50)
for rank, (energy, cid) in enumerate(conformer_energies):
    print(f"{rank:<10} {cid:<15} {energy:<25.4f}")

print("\n 1 kcal/mol (= .043 eV) represents a 16% to 84% ocupancy difference at 300 K")
print(" 1 kcal/mol -> [1/99  @ 100K]    [16/84 @ 300K]     [22/78 @ 400K]")
print(" 2 kcal/mol -> [0/100 @ 100K]    [3/97  @ 300K]     [7/93  @ 400K]")
print(" 3 kcal/mol -> [0/100 @ 100K]    [1/99  @ 300K]     [2/98  @ 400K]")

# --- 2.3 Save the Generated Conformers ---
# Save the generated conformers to an SDF file, which can store multiple conformers.
output_file = 'AllGeneratedConformers.sdf'
print(f"\nSaving conformers to {output_file}")
with Chem.SDWriter(output_file) as writer:
    for cid in cids:
        energy = results[cid][1]
        mol.SetProp('energy', f"{energy:.4f}")
        writer.write(mol, confId=cid)


# Save the Conformers to Individual .xyz Files ---
output_dir = 'GeneratedConformers_xyz'   # Create a directory to hold the .xyz files
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
print(f"Saving conformers to individual .xyz files in '{output_dir}/'")
for cid in cids:
    filename = os.path.join(output_dir, f'conformer_{cid}.xyz')  
    energy = results[cid][1]  
    Chem.MolToXYZFile(mol, filename, confId=cid)

# --- 3. Prune the Conformers Based on RMSD ---
print(f"\nStarting to prune the optimized conformers...")
print(f"Starting with {mol.GetNumConformers()} optimized conformers.")
rmsd_threshold = 0.5 
energies = [res[1] for res in results]

def prune_conformers(mol, energies, rmsd_threshold):
    sorted_cids = sorted(range(mol.GetNumConformers()), key=lambda cid: energies[cid])
    unique_cids = []
    for cid in sorted_cids:
        is_unique = True
        for unique_cid in unique_cids:
            rmsd = AllChem.GetBestRMS(mol, mol, prbId=cid, refId=unique_cid)
            if rmsd < rmsd_threshold:
                is_unique = False
                print(f"Conformer {cid} is similar to conformer {unique_cid} (RMSD: {rmsd:.4f})")
                break
        if is_unique:
            unique_cids.append(cid)
            
    new_mol = Chem.Mol(mol)
    new_mol.RemoveAllConformers()
    new_energies = []
    for unique_cid in unique_cids:
        new_mol.AddConformer(mol.GetConformer(unique_cid), assignId=True)
        new_energies.append(energies[unique_cid])
    return new_mol, new_energies

pruned_mol, pruned_energies = prune_conformers(mol, energies, rmsd_threshold)
print(f"Pruned down to {pruned_mol.GetNumConformers()} unique conformers.")

# --- 4. Save the UNIQUE Conformers ---
# (Saving unique conformers remains the same, no changes needed here)
output_dir = 'unique_conformers_xyz'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
print(f"Saving unique conformers to '{output_dir}/'")
for i in range(pruned_mol.GetNumConformers()):
    energy = pruned_energies[i]
    comment = f"Conformer {i:2}, Energy = {energy:.4f} kcal/mol"
    xyz_block = Chem.MolToXYZBlock(pruned_mol, confId=i)
    lines = xyz_block.split('\n')
    lines[1] = comment
    final_xyz_content = '\n'.join(lines)
    filename = os.path.join(output_dir, f'unique_conformer_{i}.xyz')
    with open(filename, 'w') as f:
        f.write(final_xyz_content)

# --- 5. Calculate and Print Boltzmann Probabilities ---
# Set the desired temperature in Kelvin
temperature = 298.15 # (25 degrees Celsius)

# Calculate probabilities for the unique, pruned conformers
boltzmann_probabilities100 = calculate_boltzmann_probabilities(pruned_energies, 100)
boltzmann_probabilities300 = calculate_boltzmann_probabilities(pruned_energies, 300)

# Print the results in a formatted table
print(f"\nBoltzmann Probabilities at {temperature} K:")
print("-" * 80)
print(f"{'            ':<13} {'                 ':<18} {'|T = 100 K ':<10} {'         ':<9} {'|T = 300 K ':<10} {'         ':<9}")
print(f"{'Conformer ID':<13} {'Energy (kcal/mol)':<18} {'|Prob. (%) ':<10} {'Accu. (%)':<9} {'|Prob. (%) ':<10} {'Accu. (%)':<9}")
print("-" * 80)


accu_prob_percent100 = 0.0
accu_prob_percent300 = 0.0
for i in range(pruned_mol.GetNumConformers()):
    energy = pruned_energies[i]
    prob_percent100 = boltzmann_probabilities100[i] * 100
    prob_percent300 = boltzmann_probabilities300[i] * 100
    accu_prob_percent100 += prob_percent100
    accu_prob_percent300 += prob_percent300
    print(f"{i:<13} {energy:<18.4f}  {prob_percent100:<10.2f} {accu_prob_percent100:<9.2f}  {prob_percent300:<10.2f} {accu_prob_percent300:<9.2f}")

print("\nDone.\n\n")