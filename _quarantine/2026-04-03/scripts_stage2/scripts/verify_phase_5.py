import sys
sys.path.append("src")
from akira_engine.mastery_blueprint import get_blueprint_for_mode

def verify_blueprint_overlay():
    print("--- Blueprint Overlay Verification ---")
    
    # 1. Check a mode WITHOUT calibration
    b_anthemic = get_blueprint_for_mode("anthemic_cinematic")
    print(f"MODE: anthemic_cinematic (No Calibration)")
    print(f"  Target Chorus Mora: {b_anthemic.target_chorus_mora} (Expected: 12.0)")
    
    # 2. Check the CALIBRATED mode
    b_dark = get_blueprint_for_mode("dark_cute_breakdown")
    print(f"MODE: dark_cute_breakdown (Calibrated +0.1)")
    print(f"  Target Chorus Mora: {b_dark.target_chorus_mora} (Expected: 18.1)")
    
    if abs(b_dark.target_chorus_mora - 18.1) < 0.001:
        print("\nSUCCESS: Mastery Blueprint correctly applied the Approved Overlay.")
    else:
        print("\nFAILURE: Blueprint Overlay logic is not responding.")

if __name__ == "__main__":
    verify_blueprint_overlay()
