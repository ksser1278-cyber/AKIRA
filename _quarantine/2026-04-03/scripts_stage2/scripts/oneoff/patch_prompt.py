import sys
import os

filepath = r'C:\JPop_Songwriter\AKIRA ENGINE\src\akira_engine\songwriter_v2.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """    system_body = (
        "You are a Japanese songwriter working from a structured planning document. "
        "Return markdown lyrics only. "
        "The first line must be '# <Japanese title>'. "
        "Use the exact section headers from the plan in the same order. "
        "Do not add commentary, bullet lists, or analysis prose. "
        "Write original lyrics only, never imitate or quote any living artist."
    )"""

new_block = """    demo_plan = plan.get("artist_synthesis_context", {}).get("demo_plan", {})
    archetype_context = demo_plan.get("archetype_context", {})
    identity_block = archetype_context.get("artist_sections", {}).get("Core Identity", "")
    
    system_body = (
        "You are a visionary Japanese songwriter working from a structured planning document. "
    )
    if identity_block:
        system_body += f"\\nYour Core Identity:\\n{identity_block}\\n\\n"
        
    system_body += (
        "Return markdown lyrics only. "
        "The first line must be '# <Japanese title>'. "
        "Use the exact section headers from the plan in the same order. "
        "Do not add commentary, bullet lists, or analysis prose. "
        "Write original lyrics only, never imitate or quote any living artist."
    )"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print('Successfully patched songwriter_v2.py')
else:
    print('Failed to find the old_block')
