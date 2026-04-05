import os
import subprocess

modes = ["ironic_meta", "direct_emotional_pop", "dark_cute_breakdown"]
artists = ["deco27", "kanaria", "kairiki_bear", "maretu", "pinocchiop", "iyowa", "syudou", "neru"]

env = os.environ.copy()
env["PYTHONPATH"] = r"C:\JPop_Songwriter\AKIRA ENGINE"

print("Running Mode Support Audits...")
for m in modes:
    print(f"Auditing {m}...")
    subprocess.run(["python", r"scripts\pipeline\audit_mode_support.py", "--mode-id", m], env=env, check=True)

print("\nRunning Round 2 Expansion Audits...")
for a in artists:
    print(f"Auditing {a}...")
    subprocess.run(["python", r"scripts\pipeline\audit_round2_expansion.py", "--artist-id", a], env=env, check=True)

print("ALL AUDITS COMPLETED SUCCESSFULLY.")
