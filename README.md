# Bell States & Quantum Correlation Matrix

**Quantum Computing Project using Qiskit and IBM Quantum**

## Overview

This project focuses on generating, simulating, and experimentally validating the four Bell states using Qiskit and IBM Quantum.

The main objective is to explore quantum entanglement, analyze quantum correlations, and compare theoretical predictions with results obtained from real quantum hardware.

The project covers both ideal and noisy simulations, as well as execution on an IBM Quantum processor.

## Project Objectives

- Generate the four Bell states: Φ⁺, Φ⁻, Ψ⁺, and Ψ⁻.
- Understand quantum entanglement using Hadamard and CNOT gates.
- Perform measurements in the Pauli X, Y, and Z bases.
- Calculate the 3×3 quantum correlation matrix.
- Analyze state fidelity under ideal and noisy conditions.
- Evaluate quantum correlations using the CHSH Bell inequality.
- Validate theoretical results through real IBM Quantum hardware.

## Bell States

The four Bell states are:

| State | Quantum Representation |
|---|---|
| Φ⁺ | (|00⟩ + |11⟩) / √2 |
| Φ⁻ | (|00⟩ − |11⟩) / √2 |
| Ψ⁺ | (|01⟩ + |10⟩) / √2 |
| Ψ⁻ | (|01⟩ − |10⟩) / √2 |

## Technologies Used

- **Python** – Main programming language
- **Qiskit** – Quantum circuit construction and simulation
- **Qiskit Aer** – Quantum circuit simulation and noise modeling
- **IBM Quantum** – Real quantum hardware execution
- **Qiskit IBM Runtime** – Communication with IBM Quantum backends
- **NumPy / SciPy** – Numerical calculations and matrix analysis
- **Matplotlib** – Data visualization and experimental results

## Experimental Analysis

The project investigates several important quantum computing concepts:

### 1. Quantum Correlation Matrix

Measurements are performed across nine combinations of Pauli bases (XX, XY, XZ, ..., ZZ) to construct the correlation matrix:

T[a][b] = ⟨σa ⊗ σb⟩

### 2. Quantum State Fidelity

The fidelity of each Bell state is evaluated under ideal simulation, noisy simulation, and real hardware execution.

### 3. CHSH Bell Inequality

The CHSH parameter is calculated to investigate the violation of the classical limit and demonstrate quantum correlations.

### 4. Real Hardware Validation

The theoretical and simulated results are compared with measurements obtained from IBM Quantum hardware, highlighting the effects of physical quantum noise.

## Installation

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
cd YOUR_REPOSITORY_NAME
```

Install the required dependencies:

```bash
pip install qiskit qiskit-aer numpy scipy matplotlib
```

For IBM Quantum execution:

```bash
pip install qiskit-ibm-runtime
```

## Running the Project

Run the ideal simulation:

```bash
python bell_states.py
```

Run the simulation with a 4% noise model:

```bash
python bell_states.py --noise 0.04
```

Execute the experiment on IBM Quantum hardware:

```bash
python bell_states.py --backend ibm
```

## Results

The project demonstrates:

- Successful generation of all four Bell states.
- Distinct correlation matrix signatures for each state.
- High fidelity in ideal and noisy simulations.
- Violation of the CHSH classical limit.
- Experimental validation using real IBM Quantum hardware.

Experimental results are automatically stored in `rezultate.json` and represented graphically.

## Author

**Penoiu Cristian**

Faculty of Automation, Computers and Electronics  
Computer Engineering – SCTC

## Acknowledgements

This project was developed for educational and experimental purposes as an exploration of quantum computing, quantum entanglement, and quantum information processing using Qiskit and IBM Quantum.
