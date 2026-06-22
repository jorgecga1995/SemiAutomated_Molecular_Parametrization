import psi4
import os
import numpy as np

# Set the charge, multiplicity, and molecular geometry
mol_charge = 0
mol_multiplicity = 1

geom_directory = "/p/home/jorgecga/SwitchesFor-aRuCl3/..."
geom_file = "mol_afterPBE0_Opt0.xyz"
geom_path = os.path.join(geom_directory, geom_file)

psi4.set_output_file('1.1_OptFreq_out.dat', False) 

# Resources setup
# Wheat resources
# *****************************************************************************
# * System Name (Model)           Compute Nodes   Cores/Node   Avail_Mem/Node *
# * wheat (Liqid Matrix XT-4)                                                 *
# *    Standard                        770             92           356 GB    *
# *    Bigmem                            7             92          3000 GB    *
# *    GPU                              16             92           731 GB    *
# *    MLA+4                            64             92           731 GB    *
# *    MLA+6                            32             92           731 GB    *
# *****************************************************************************


# --- Basic Setup for Psi4 ---
psi4.set_num_threads(92) # The number of threads should match the number of cores you request on the HPC.
psi4.set_memory('350 GB')

# Set global options for the calculation.
psi4.set_options({
    'basis': 'def2-tzvpd',

    'dft_spherical_points': 770,
    'dft_radial_points': 100,
    'dft_pruning_scheme': 'robust',     # Generally safe and will speed things up

    'g_convergence': 'QCHEM',   # 'NWCHEM_LOOSE',
    'geom_maxiter': 200,

    # --- SCF Convergence ---
    'e_convergence': 1e-8,
    'd_convergence': 1e-8
})
# Set reference based on multiplicity
# if mol_multiplicity == 1:
#     psi4.set_options({'reference': 'rhf'})
# else:
#     psi4.set_options({'reference': 'uhf'})

if mol_multiplicity == 1:
    psi4.set_options({'reference': 'rks'})
else:
    psi4.set_options({'reference': 'uks'})

# --- Read Geometry from an .xyz File ---
print("\nStarting optimization from {}".format(geom_file))
with open(geom_path, 'r') as f:
    xyz_from_file = f.read()  # Read the entire .xyz file into a string

mol = psi4.geometry(xyz_from_file)
mol.set_molecular_charge(mol_charge)  # set charge and multiplicity if the .xyz does not contain them.
mol.set_multiplicity(mol_multiplicity)

GeomConverged = False
Opt_Freq_iterations = 0
while not GeomConverged and Opt_Freq_iterations < 5:
    # ====================================================================================================================================================
    optimized_energy_xyz = psi4.optimize('m062x', molecule=mol)

    print("...Optimization finished!")
    print(f"Electronic Energy after m062x optimization {Opt_Freq_iterations}: {optimized_energy_xyz:.8f} Hartrees")
    DFT_OptGeom_file = f'1.1_mol_after_M062X_Opt{Opt_Freq_iterations}.xyz'
    mol.save_xyz_file(DFT_OptGeom_file, 1)

    # ====================================================================================================================================================
    print("\nStarting Frequency Calculation")
    freq_energy, wfn = psi4.frequency('m062x', molecule=mol, return_wfn=True)   # Run the frequency calculation
    print("...Frequency calculation finished!")

    frequencies = wfn.frequencies().to_array()
    imaginary_freqs = [f for f in frequencies if f < 0]

    if not imaginary_freqs:
        print("\n Success! No imaginary frequencies found. The structure is a true minimum.")
        GeomConverged = True
    else:
        print(f"\n Warning! Found {len(imaginary_freqs)} imaginary frequencies:")
        for f in imaginary_freqs:
            print(f"   {f:.2f} cm^-1")

        vibinfo = wfn.frequency_analysis      # 3. Access the vibrational analysis dictionary
        modes = vibinfo['x'].data
        # The mode is a 1D column of length 3N -> reshape it to (N_atoms, 3)
        imaginary_mode = modes[:, 0].reshape(-1, 3)
        # Save the reshaped array to a text file
        IM_file = f"1.1_i_mode_displacements_M062X_{Opt_Freq_iterations}.txt"  # Define the filename
        # 'fmt' defines the decimal precision, 'header' adds a descriptive first line
        np.savetxt(
            IM_file, 
            imaginary_mode, 
            fmt='%12.8f', 
            header='X-Displacement | Y-Displacement | Z-Displacement (Bohr)'
        )
        print(f"Imaginary mode displacements have been saved to: {IM_file}")

        # 6. Perturb the geometry
        # Get current Cartesian coordinates (PSI4 stores these internally in Bohr)
        current_geom = np.array(mol.geometry())
        step_size = 0.2 # step size to push it off the saddle point.

        new_geom = current_geom + (step_size * imaginary_mode)

        mol.set_geometry(psi4.core.Matrix.from_array(new_geom)) # Update the PSI4 molecule object with the new coordinates

    # ====================================================================================================================================================
    Opt_Freq_iterations += 1


# ====================================================================================================================================================
# --- Clean up scratch files ---
psi4.core.clean()






