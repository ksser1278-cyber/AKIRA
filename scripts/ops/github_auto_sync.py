import subprocess
import datetime
import os

def run_command(command, cwd=None):
    try:
        result = subprocess.run(
            command, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}:\n{e.stderr}")
        return None

def main():
    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print(f"[{datetime.datetime.now()}] Starting sync for {repo_dir}")
    
    status = run_command(["git", "status", "--porcelain"], cwd=repo_dir)
    
    if status is None:
        print("Failed to run git status. Ensure you have git installed and are in a git repository.")
        return

    if not status:
        print(f"[{datetime.datetime.now()}] No changes to sync.")
        return
        
    print(f"[{datetime.datetime.now()}] Changes detected:\n{status}")
    print(f"[{datetime.datetime.now()}] Staging files...")
    
    run_command(["git", "add", "."], cwd=repo_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"auto: sync engine state [{timestamp}]"
    
    print(f"[{datetime.datetime.now()}] Committing...")
    run_command(["git", "commit", "-m", commit_msg], cwd=repo_dir)
    
    print(f"[{datetime.datetime.now()}] Pushing to remote...")
    push_output = run_command(["git", "push"], cwd=repo_dir)
    
    if push_output is not None:
        print(f"[{datetime.datetime.now()}] Sync completed successfully.")
    else:
        print(f"[{datetime.datetime.now()}] Sync failed during push.")

if __name__ == "__main__":
    main()
