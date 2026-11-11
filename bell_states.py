#!/usr/bin/env python3
"""
Curs 2 - Fundamente matematice si entanglement cuantic
Tema 1: Generarea si testarea starilor Bell + matricea de corelatie

Ce face scriptul:
  1. Construieste cele 4 stari Bell (Phi+, Phi-, Psi+, Psi-).
  2. Le ruleaza pe un simulator (Qiskit Aer) sau pe hardware IBM Quantum.
  3. Masoara fiecare pereche de qubiti in bazele X, Y, Z (9 combinatii).
  4. Calculeaza matricea de corelatie T_ij = <sigma_i (x) sigma_j>  (3x3),
     fidelitatea starii si valoarea maxima CHSH (testul Bell).
  5. Salveaza grafice (PNG) si rezultatele (JSON).

Utilizare:
  python bell_states.py                      # simulator ideal
  python bell_states.py --noise 0.02         # simulator cu zgomot depolarizant
  python bell_states.py --backend ibm        # hardware real IBM (necesita cont)
"""
import argparse
import itertools
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit, transpile

# --------------------------------------------------------------------------
# 1. Starile Bell
# --------------------------------------------------------------------------
BELL_STATES = {
    "Phi+": "(|00> + |11>)/sqrt(2)",
    "Phi-": "(|00> - |11>)/sqrt(2)",
    "Psi+": "(|01> + |10>)/sqrt(2)",
    "Psi-": "(|01> - |10>)/sqrt(2)",
}

# Nume frumoase pentru grafice (evita ca matplotlib sa interpreteze "->" ca sageata)
PRETTY = {"Phi+": "Φ⁺", "Phi-": "Φ⁻", "Psi+": "Ψ⁺", "Psi-": "Ψ⁻"}
PRETTY_FORMULA = {
    "Phi+": "(|00⟩ + |11⟩)/√2", "Phi-": "(|00⟩ − |11⟩)/√2",
    "Psi+": "(|01⟩ + |10⟩)/√2", "Psi-": "(|01⟩ − |10⟩)/√2",
}

# Matricea de corelatie IDEALA (diagonala) pentru fiecare stare, baza (X, Y, Z)
IDEAL_DIAG = {
    "Phi+": (1, -1, 1),
    "Phi-": (-1, 1, 1),
    "Psi+": (1, 1, -1),
    "Psi-": (-1, -1, -1),
}


def bell_circuit(name: str) -> QuantumCircuit:
    """Circuitul care pregateste starea Bell `name` pe qubitii 0 si 1."""
    qc = QuantumCircuit(2, name=name)
    if name in ("Phi-", "Psi-"):
        qc.x(0)                      # semn minus
    if name == "Psi+":
        qc.x(1)                      # |01> in loc de |00>
    if name == "Psi-":
        qc.x(1)
    qc.h(0)                          # superpozitie
    qc.cx(0, 1)                      # entanglement (CNOT)
    return qc


# --------------------------------------------------------------------------
# 2. Masurarea in bazele X / Y / Z
# --------------------------------------------------------------------------
def with_measurement(base: QuantumCircuit, bases: str) -> QuantumCircuit:
    """Adauga rotatia de baza + masurarea. bases = ex. 'XZ' (qubit0=X, qubit1=Z)."""
    qc = base.copy()
    qc.name = f"{base.name}_{bases}"
    for q, b in enumerate(bases):
        if b == "X":
            qc.h(q)
        elif b == "Y":
            qc.sdg(q)
            qc.h(q)
    qc.measure_all()
    return qc


# --------------------------------------------------------------------------
# 3. Corelatii din rezultate
# --------------------------------------------------------------------------
def correlation(counts: dict, i: int, j: int) -> float:
    """E[(-1)^(b_i XOR b_j)] pentru qubitii i si j (Qiskit: bitul 0 = cel din dreapta)."""
    total = sum(counts.values())
    e = 0
    for bitstring, c in counts.items():
        bits = bitstring.replace(" ", "")[::-1]       # bits[k] = qubitul k
        e += c * (-1) ** (int(bits[i]) ^ int(bits[j]))
    return e / total


def correlation_matrix(all_counts: dict, i: int, j: int) -> np.ndarray:
    """T[a][b] = <sigma_a (qubit i) x sigma_b (qubit j)>, a,b in {X,Y,Z}."""
    labels = "XYZ"
    T = np.zeros((3, 3))
    for a, la in enumerate(labels):
        for b, lb in enumerate(labels):
            T[a, b] = correlation(all_counts[la + lb], i, j)
    return T


def fidelity(T: np.ndarray, name: str) -> float:
    """F = <psi|rho|psi> = (1 + sum_k t_k * T_kk) / 4  (t_k = semnele ideale)."""
    return (1 + sum(t * T[k, k] for k, t in enumerate(IDEAL_DIAG[name]))) / 4


def chsh_max(T: np.ndarray) -> float:
    """Criteriul Horodecki: S_max = 2*sqrt(suma celor mai mari 2 val. proprii ale T^T T)."""
    w = np.sort(np.linalg.eigvalsh(T.T @ T))[::-1]
    return 2 * np.sqrt(w[0] + w[1])


# --------------------------------------------------------------------------
# 4. Backend: simulator sau IBM Quantum
# --------------------------------------------------------------------------
def get_runner(args):
    """Returneaza o functie run(circuits) -> lista de dictionare `counts`."""
    if args.backend == "ibm":
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
        service = QiskitRuntimeService()   # dupa: QiskitRuntimeService.save_account(token=...)
        backend = service.least_busy(operational=True, simulator=False, min_num_qubits=2)
        print(f"[IBM] Backend ales: {backend.name}")
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
        sampler = Sampler(mode=backend)

        def run(circuits):
            isa = pm.run(circuits)
            job = sampler.run(isa, shots=args.shots)
            print(f"[IBM] Job id: {job.job_id()} (poate astepta in coada...)")
            res = job.result()
            return [r.data.meas.get_counts() for r in res]
        return run

    from qiskit_aer import AerSimulator
    noise_model = None
    if args.noise > 0:
        from qiskit_aer.noise import NoiseModel, depolarizing_error
        noise_model = NoiseModel()
        noise_model.add_all_qubit_quantum_error(depolarizing_error(args.noise / 10, 1), ["h", "sdg", "x"])
        noise_model.add_all_qubit_quantum_error(depolarizing_error(args.noise, 2), ["cx"])
    sim = AerSimulator(noise_model=noise_model, seed_simulator=args.seed)

    def run(circuits):
        t = transpile(circuits, sim)
        result = sim.run(t, shots=args.shots).result()
        return [result.get_counts(i) for i in range(len(circuits))]
    return run


# --------------------------------------------------------------------------
# 5. Grafice
# --------------------------------------------------------------------------
def save_circuits(outdir):
    fig, axes = plt.subplots(2, 2, figsize=(10, 4.6))
    for ax, name in zip(axes.ravel(), BELL_STATES):
        bell_circuit(name).draw("mpl", ax=ax, style="iqp")
        ax.set_title(f"|{PRETTY[name]}⟩ = {PRETTY_FORMULA[name]}", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "circuite_bell.png"), dpi=200)
    plt.close(fig)


def save_histograms(results, outdir):
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.4), sharey=True)
    for ax, (name, r) in zip(axes, results.items()):
        counts = r["counts_ZZ"]
        keys = ["00", "01", "10", "11"]
        shots = sum(counts.values())
        vals = [counts.get(k, 0) / shots for k in keys]
        ax.bar(keys, vals, color=["#2a9d8f", "#e76f51", "#e76f51", "#2a9d8f"])
        ax.set_title(f"|{PRETTY[name]}⟩")
        ax.set_xlabel("rezultat (q1 q0)")
        ax.set_ylim(0, 0.7)
    axes[0].set_ylabel("probabilitate")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "histograme_bell.png"), dpi=200)
    plt.close(fig)


def save_heatmaps(results, outdir):
    fig, axes = plt.subplots(1, 4, figsize=(15, 3.8))
    for ax, (name, r) in zip(axes, results.items()):
        T = np.array(r["T"])
        im = ax.imshow(T, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(3), ["X", "Y", "Z"])
        ax.set_yticks(range(3), ["X", "Y", "Z"])
        ax.set_xlabel("baza qubit 1")
        ax.set_ylabel("baza qubit 0")
        ax.set_title(f"|{PRETTY[name]}⟩   F={r['fidelity']:.3f}")
        for a in range(3):
            for b in range(3):
                ax.text(b, a, f"{T[a, b]:+.2f}", ha="center", va="center",
                        color="white" if abs(T[a, b]) > 0.55 else "black", fontsize=10)
    fig.colorbar(im, ax=axes, shrink=0.8, label="<sigma_a x sigma_b>")
    fig.savefig(os.path.join(outdir, "matrici_corelatie.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_chsh(results, outdir):
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    names = list(results)
    s = [results[n]["chsh_max"] for n in names]
    ax.bar([PRETTY[n] for n in names], s, color="#264653")
    ax.axhline(2, color="#e76f51", ls="--", label="limita clasica (2)")
    ax.axhline(2 * np.sqrt(2), color="#2a9d8f", ls="--", label="limita Tsirelson (2√2≈2.83)")
    ax.set_ylim(0, 3.9)
    ax.set_ylabel("S maxim (CHSH)")
    ax.legend(loc="upper center", fontsize=8, ncol=1)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "chsh.png"), dpi=200)
    plt.close(fig)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Stari Bell + matrice de corelatie")
    ap.add_argument("--backend", choices=["sim", "ibm"], default="sim")
    ap.add_argument("--shots", type=int, default=4096)
    ap.add_argument("--noise", type=float, default=0.0, help="eroare depolarizanta CNOT (ex. 0.02)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--outdir", default="rezultate")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    run = get_runner(args)
    settings = ["".join(p) for p in itertools.product("XYZ", repeat=2)]   # XX, XY, ..., ZZ

    # un singur batch cu toate cele 4 x 9 = 36 circuite
    circuits, index = [], []
    for name in BELL_STATES:
        base = bell_circuit(name)
        for s in settings:
            circuits.append(with_measurement(base, s))
            index.append((name, s))
    all_counts = run(circuits)

    results = {}
    for (name, s), counts in zip(index, all_counts):
        results.setdefault(name, {"raw": {}})["raw"][s] = counts

    for name, r in results.items():
        # In acest exemplu avem 2 qubiti => o singura pereche (0,1).
        # Codul e general: pentru n qubiti se itereaza peste combinations(range(n), 2).
        pairs = {}
        for (i, j) in itertools.combinations(range(2), 2):
            pairs[f"q{i}-q{j}"] = correlation_matrix(r["raw"], i, j)
        T = pairs["q0-q1"]
        r["T"] = T.tolist()
        r["fidelity"] = float(fidelity(T, name))
        r["chsh_max"] = float(chsh_max(T))
        r["counts_ZZ"] = r["raw"]["ZZ"]

        print(f"\n=== |{name}> = {BELL_STATES[name]} ===")
        print("Matricea de corelatie T (linii: baza q0, coloane: baza q1; ordine X, Y, Z):")
        print(np.array2string(T, precision=3, suppress_small=True))
        print(f"Fidelitate = {r['fidelity']:.4f}   |   S_max(CHSH) = {r['chsh_max']:.4f}"
              f"  ({'VIOLARE Bell' if r['chsh_max'] > 2 else 'fara violare'})")

    save_circuits(args.outdir)
    save_histograms(results, args.outdir)
    save_heatmaps(results, args.outdir)
    save_chsh(results, args.outdir)

    with open(os.path.join(args.outdir, "rezultate.json"), "w") as f:
        json.dump({n: {k: v for k, v in r.items() if k != "raw"} for n, r in results.items()}, f, indent=2)
    print(f"\nGrafice si rezultate salvate in: {args.outdir}/")


if __name__ == "__main__":
    main()
