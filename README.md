# Semi-Automated Molecule Parametrization Pipeline 🧪💻

This repository contains a suite of Python scripts to parametrize a large set of molecules for classical Molecular Dynamics (MD) simulations. It handles initial conformer generation, DFT optimization, ESP calculations, and AMBER parameter generation.

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

## 🚀 Workflow Execution Steps

### Step 0: Initial Conformer Search (RDKit)
This step is currently run manually per molecule inside `0_ConformerSearch`.

* Scripts: `0_conformer_search.py` and `0_RDKit_Sub.sh`

* Process:

    1. Takes a SMILES string, `.mol`, or `.mol2` file.
    2. Generates isomers and conformers using `RDKit`, reporting interpreted charge and `SA_score`.
    3. Minimizes geometry with MMFF94 or UFF.
    4. Prunes similar conformers (RMSD < 0.5 Å) and saves unique geometries to /unique_conformers_xyz/.
    5. Reports conformer energies (kcal/mol) and population analysis (100K and 300K).

---

All other scripts are meant to be run from the current directory, though they are stored in the `./scripts/` folder. 

---
### Step 1: DFT Optimization & Frequency (Gaussian 16)
Optimizes the selected conformers using the `M06-2X/6-311G(2df,p)` level of theory (`6-311+G(2df,p)` for anions).

* `1_GenerateDFTOptInputScripts.py`: Generates Gaussian `.com` files and PBS `.sh` submission scripts in `1_DFT_opt/conformer{ID}/Gauss/`.

* `2_SubmitSeveralOpt.py`: Automatically submits all generated jobs (`qsub gaussSub.sh`).

* `3_check_Gaussian_logs.py`: Parses `.log` files to verify that all frequencies are real (true minima).

* Troubleshooting Imaginary Frequencies:

    * If transition states are detected, use `3.4_TestFreqAtFinerGrid.py` to create a `SuperFineGrid_FreqTest` folder.

    * Submit using `3.5_SubmitTheFreqCopyingCHK.py`.

**Note**: `PSI4` fallback templates are provided in `./00_template/1_DFT_opt/conformer0/` if a geometry refuses to optimize to a minimum.

---
### Step 2: ESP Calculations

Calculates the Electrostatic Potential (ESP) at the optimized geometries using MP2/aug-cc-pVTZ.   
* `4_CreateMP2_ESP_input.py`: Creates inputs in 3_Parametrization/Gauss-Ante/conformer{ID}/.
* `5_MP2_ESP_SubmissionCopyingCHK.py`: Submits the ESP jobs.

---
### Step 3: Parametrization (Antechamber)
Processes the ESP `.log` files to generate AMBER parameters (RESP charges + GAFF2).

* `6_CreateAntechamberInput.py`: Creates Antechamber submission scripts for each conformer.

* `7_Sub_Antechamber.py`: Submits the Antechamber jobs.


---
#### Final Outputs: `ABC.pdb`, `ABC.prepi`, and `ABC.frcmod` containing the RESP charges and GAFF2 parameters.
---


## 🛠️ Built With & Acknowledgments

This pipeline relies on several open-source software packages:

| Software | Purpose | Repository / Website | Citation |
|---|---|---|---|
| **RDKit** | Cheminformatics, conformer generation, and structure manipulation. | [RDKit GitHub](https://github.com/rdkit/rdkit) | [Citation](https://www.rdkit.org) |
| **Psi4** | Ab initio quantum chemistry, geometry optimization, ESP calculations. | [Psi4 GitHub](https://github.com/psi4/psi4) | [Psi4 Publication](https://doi.org/10.1063/5.0006002) |
| **resp** | Implementation of the RESP algorithm in python | [resp GitHub](https://github.com/cdsgroup/resp) | [resp Publication](https://doi.org/10.1002/qua.26035) |
| **Antechamber** | Parameter generation and residue topology creation (part of AmberTools). | [AmberTools Website](https://ambermd.org/AmberTools.php) | [Amber Citation](https://doi.org/10.1021/acs.jcim.5c01063) |

We are grateful to the developers and maintainers of these projects for making their tools freely available.

---

[![Powered by RDKit](https://img.shields.io/badge/Powered%20by-RDKit-3838ff.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAFVBMVEXc3NwUFP8UPP9kZP+MjP+0tP////9ZXZotAAAAAXRSTlMAQObYZgAAAAFiS0dEBmFmuH0AAAAHdElNRQfmAwsPGi+MyC9RAAAAQElEQVQI12NgQABGQUEBMENISUkRLKBsbGwEEhIyBgJFsICLC0iIUdnExcUZwnANQWfApKCK4doRBsKtQFgKAQC5Ww1JEHSEkAAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyMi0wMy0xMVQxNToyNjo0NyswMDowMDzr2J4AAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjItMDMtMTFUMTU6MjY6NDcrMDA6MDBNtmAiAAAAAElFTkSuQmCC)](https://www.rdkit.org/)
    
