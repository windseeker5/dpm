import subprocess
import sys
import os

# Change to the app directory
os.chdir('/home/kdresdell/Documents/DEV/minipass_env/app')

# Run the extraction script
try:
    result = subprocess.run([sys.executable, 'extract_ticket_image.py'], 
                          capture_output=True, text=True, check=True)
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
except subprocess.CalledProcessError as e:
    print(f"Script failed with return code {e.returncode}")
    print("STDOUT:", e.stdout)
    print("STDERR:", e.stderr)