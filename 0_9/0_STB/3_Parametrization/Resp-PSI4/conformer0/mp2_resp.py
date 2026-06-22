import psi4
import resp
import os

# --- Basic Setup for Psi4 ---
psi4.set_num_threads(92) # The number of threads should match the number of requested cores on the HPC.
psi4.set_memory('350 GB')

# psi4.set_output_file('MP2RESPtest.dat', False) 

# Set the charge, multiplicity, and molecular geometry
mol_charge = 0
mol_multiplicity = 1

mol = psi4.geometry("""
C          1.924618   -0.203780    0.022703
C         -1.924635    0.203863    0.022816
C          0.480851   -0.462307    0.023941
C         -0.480880    0.462464    0.024135
C          2.472699    1.032220    0.376965
C         -2.472641   -1.032163    0.377097
C          2.796288   -1.230964   -0.342633
C         -2.796354    1.230973   -0.342610
C          3.840626    1.235839    0.341724
C         -3.840551   -1.235892    0.341763
C          4.166703   -1.028428   -0.378419
C         -4.166749    1.028325   -0.378490
C          4.694522    0.208109   -0.039567
C         -4.694496   -0.208243   -0.039634
H          0.202881   -1.511992   -0.015319
H         -0.202953    1.512174   -0.014722
H          1.823190    1.834551    0.704297
H         -1.823080   -1.834411    0.704534
H          2.386440   -2.198695   -0.609459
H         -2.386561    2.198727   -0.609440
H          4.246609    2.199579    0.623162
H         -4.246480   -2.199648    0.623223
H          4.823532   -1.838533   -0.669788
H         -4.823623    1.838367   -0.669936
H          5.764743    0.369604   -0.062587
H         -5.764703   -0.369820   -0.062725
""")

mol.update_geometry()

mol.set_molecular_charge(mol_charge)  # set charge and multiplicity if the .xyz does not contain them.
mol.set_multiplicity(mol_multiplicity)

options = {'VDW_SCALE_FACTORS'  : [1.4, 1.526, 1.652, 1.778, 1.904, 2.03, 2.156, 2.282, 2.408, 2.534],
           'VDW_POINT_DENSITY'  : 17.0,
           'RESP_A'             : 0.0005,
           'RESP_B'             : 0.1,
           'METHOD_ESP'         : 'mp2',
           'BASIS_ESP'          : 'aug-cc-pVTZ'
           }

# Call for first stage fit
charges1 = resp.resp([mol], options)
print('Electrostatic Potential Charges')
print(charges1[0])
print('Restrained Electrostatic Potential Charges')
print(charges1[1])

options['grid'] = ['1_%s_grid.dat' %mol.name()]
options['esp'] = ['1_%s_grid_esp.dat' %mol.name()]

# # Specify additional intramolecular constraints
# # (i.e. both O (ids 7 and 9) should have equal charges,
# #   both hydroxyl H (ids 8 and 10) should equal charges,
# #   both C (ids 1 and 4) should have equal charges, and
# #   all four aliphatic H (ids 2, 3, 5 and 6) should have equal charges)
# options["constraint_group"] = [[7, 9], [8, 10], [1, 4], [2, 3, 5, 6]]

# Add constraint for atoms fixed in second stage fit
# constraint_charge = []
# for i in range(4, 8):
#     constraint_charge.append([charges1[1][i], [i+1]])
# options['constraint_charge'] = constraint_charge
# options['constraint_group'] = [[2, 3, 4]]

# options["constraint_group"] = [[1, 2], [5, 6, 7]]
options['RESP_A'] = 0.001

# Call for second stage fit
charges2 = resp.resp([mol], options)



# Get RESP charges
print("\nStage Two:\n")
print('RESP Charges')
print(charges2[1])
