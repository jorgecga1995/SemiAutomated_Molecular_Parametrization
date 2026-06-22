# Semi-automated molecule parametrization 🧪💻

This repository contains scripts to parametrize a large set of molecules to conduct Molecular Dynamics (MD) 


## 📋 Prerequisites & Environment

* **Environment:** DoD HPC environment utilizing the **PBS** queue system (`qsub`).
* **Software:** Gaussian 16 (`g16`), RDKit, Antechamber (AmberTools), PSI4 (optional fallback).
* **Python:** Python 3.6+ with standard libraries (`os`, `glob`, `re`, `subprocess`, `shutil`).

---

## 📂 Naming Conventions & Directory Architecture

Molecules are assigned an ID and a 3-letter code: `00_ABC`, where `00` is the ID, currently from 0–101, and `ABC` is the unique residue name for AMBER. (`BC` could also be digits). 
To prevent directory clutter, molecules are grouped in subfolders by tens based on their ID (e.g., `./0_9/`, `./10_19/`).

```text
.
├── README.md
├── mol_conf_list.txt                    <-- Master control list
├── 0_9/                                 <-- First layer (grouped by tens)
│   ├── 0_STB/                           <-- Second layer (Molecule directory)
│   │   ├── 0_ConformerSearch/           <-- Initial .xyz coords & RDKit outputs
│   │   ├── 1_DFT_opt/                   <-- Gaussian 16 opt/freq jobs
│   │   └── 3_Parametrization/           <-- ESP and Antechamber outputs
│   └── 1_SSB/
└── 10_19/...
```

## ⚙️ The Master List: mol_conf_list.txt
The pipeline is driven by a master text file that dictates which molecules and conformers to process.

**Formatting Rules:**
* Molecules are separated by an empty line.
* Line 1: Molecule ID (e.g., 0).
* Line 2: Charge (e.g., c 0 or c -1).
* Lines 3+: Conformer IDs to process. (You can add 'no' next to a conformer to skip it).

Example:
```text
0
c 0
0
1

1
c -1
0 no
1
2
```

Several files can be created with this format to automate different tasks.

## 🚀 Workflow Execution Steps

### Step_0

* Molecules are labeled `00_ABC`, where `00` is a number serving as ID (currently in the range 0 - 101) and `ABC` are three alphanumeric characters that will uniquely denote the residue name in Amber input files (`A` should be a letter). 
* All calculations corresponding to a given molecule are carried out in a directory of the same name. 
* Molecules are grouped in subsets of 10, according to their ID, so directories: 

    `./0_9/` would contain molecules `0_STB`  `1_SSB`  ... `9_BMD`   
    `./10_19/` would have `10_DHD`  `11_OFD` ... `19_HBB`  
    and so on  

* Inside each `00_ABC` molecular directory there should be an initial `0_ConformerSearch` folder (for example `./0_9/0_STB/0_ConformerSearch/`) containing two files:    
    * `0_conformer_search.py`   
    * `0_RDKit_Sub.sh`         

* `0_RDKit_Sub.sh` is a PBS submission script for `0_conformer_search.py`   
* `0_conformer_search.py` conducts the initial step of the parametrization (as indicated by the `0_` prefix). It takes as input a `SMILES` string, or the path to a `.mol`, `.mol2`, or similar files. It:
    * uses RDKit
    * reports the charge it interpreted the molecule to have
    * reports a `SA_score` for the molecule
    * generates molecular isomers, and conformers for each isomer 
        * The number of conformers can be adjusted based on the number of rotatable bonds detected
    * Each conformer geometry is minimized with either `MMFF94` or `UFF`. The resulting geometries are saved as xyz files in a `/GeneratedConformers_xyz/` folder. (for example `./0_9/0_STB/0_ConformerSearch/GeneratedConformers_xyz/`) 

    * Conformers of similar geometry are pruned using an RMSD of 0.5 Å as threshold

    * All resulting 'unique' conformer geometries are saved as xyz files inside the folder `/unique_conformers_xyz/` (for example `./0_9/0_STB/0_ConformerSearch/unique_conformers_xyz/`)   

    * Conformer energies are reported in kcal/mol 
    * Population analysis at T=100K and T=300K are also shown

The output of `0_conformer_search.py` is stored in `rdkit.oe`.
The filename can be adjusted in `0_RDKit_Sub.sh`.

Currently, the execution of the initial step is not automated. We manually select a number of conformers for each molecule that would be further processed. These are listed in a file like:
    `mol_conf_list.txt`

---
### Step_1

After a list of molecules and conformers is generated, we proceed to optimize the conformers using DFT. 
This will be done inside each molecular folder, in a subfolder named `1_DFT_opt`.

It is possible to use `PSI4` for the task. Scripts are provided inside `./00_template/1_DFT_opt/conformer0/`, but it hasn't been automated that way. 

Using `Gaussian 16` it is just a matter of running script `1_GenerateDFTOptInputScripts.py`. The script takes as input a list like `mol_conf_list.txt`

This would create a  `/00_ABC/1_DFT_opt/conformer{conf_ID}/Gauss/` subfolder structure, with the `Gauss` folder containing the files:   
* `gaussSub.sh`, a submission script     
* `00_ABC_c{conf_ID}.com`, input for the Gaussian 16 optimization job.

Currently the `M06-2X/6-311G(2df,p)` level of theory is used (`6-311+G(2df,p)` for anions). Frequency calculations are also included. 

The script `2_SubmitSeveralOpt.py` submits all the calculations (`qsub gaussSub.sh`) it also requires a list like `mol_conf_list.txt`


* `3_check_Gaussian_logs.py` checks that all frequencies are real. 
    * It also uses a list like `mol_conf_list.txt` to loop over all conformers of all molecules.

If some imaginary frequencies are detected, 
* `3.4_TestFreqAtFinerGrid.py` can be used to generate test freq calculations using a tighter grid. It
    * uses a list like `mol_conf_list.txt` with the affected conformers. 
    * creates an extra `/00_ABC/1_DFT_opt/conformer{conf_ID}/Gauss/SuperFineGrid_FreqTest/` folder for affected conformers containing a submission script an an input file. 
    * `3.5_SubmitTheFreqCopyingCHK.py` submits the corresponding calculations 

For geometries that continue to be in a transition state, the `PSI4` scripts may be useful as they use the normal mode corresponding to the first imaginary frequency to update the molecular geometry in a loop of opt and freq calcualtions.  

---
### Step_2
In this step an ESP calculation is performed at the optimized geometries obtained in the previous step. We have been using the `MP2/aug-cc-pVTZ` level of theory.

For each conformer specified in a list like `mol_conf_list.txt`:
* `4_CreateMP2_ESP_input.py` creates a submission script and a gaussian input within a `/00_ABC/3_Parametrization/Gauss-Ante/conformer{conf_ID}/` subfolder.  
* `5_MP2_ESP_SubmissionCopyingCHK.py` submits the corresponding calculations.

---
### Step_3

The ESP calculations result in `00_ABC_c{conf_ID}.log` output files. These are processed by `Antechamber` to create `ABC.pdb`, `ABC.prepi`, and `ABC.frcmod` files. 
* `6_CreateAntechamberInput.py` creates the required submission script for all conformers listed in a `mol_conf_list.txt`-equivalent text file
* `7_Sub_Antechamber.py` submits all those jobs.

For a given `00_ABC` molecule, this result in `ABC.pdb`, `ABC.prepi` files with (in principle) different RESP charges for each conformer.  
All other parameters are obtained from the GAFF2 force field. 

The calculations described in Steps 2 and 3 to obtain RESP charges can also be performed with `PSI4`, though it hasn't been automated.  

---






