import os
import subprocess

env = os.environ.copy()
env["PYTHONPATH"] = r"C:\JPop_Songwriter\AKIRA ENGINE"

modes = ["ironic_meta", "direct_emotional_pop", "dark_cute_breakdown"]
artists = ["deco27", "kanaria", "kairiki_bear", "maretu", "pinocchiop", "iyowa", "syudou", "neru"]

print("Merging Mode Support...")
for m in modes:
    in_dir = os.path.join(r"data\_global\mode_support", m, r"external_handoff\incoming")
    if os.path.exists(in_dir):
        subprocess.run(["python", r"scripts\pipeline\merge_mode_support_external.py", "--mode-id", m, "--input-dir", in_dir], env=env, check=False)

print("\nMerging Round 2 Expansion Data...")
for a in artists:
    in_dir = os.path.join(r"data\_global\round2_expansion", a, "incoming")
    if os.path.exists(in_dir):
        subprocess.run(["python", r"scripts\pipeline\merge_round2_external.py", "--artist-id", a, "--input-dir", in_dir], env=env, check=False)

print("\nMerging Round 2 Seed Data...")
for a in artists:
    in_dir = os.path.join(r"data\_global\round2_expansion", a, "seed_incoming")
    if os.path.exists(in_dir):
        subprocess.run(["python", r"scripts\pipeline\merge_round2_seed_external.py", "--artist-id", a, "--input-dir", in_dir], env=env, check=False)

print("ALL MERGES COMPLETED.")
