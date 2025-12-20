import subprocess
import sys
import os
import shutil

def install_requirements():
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def build_exe():
    print("Building executable...")
    # PyInstaller command
    # --noconfirm: overwrite output directory without asking
    # --onefile: create a single executable file
    # --windowed: do not show a console window (GUI app)
    # --name: name of the executable
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "SMBX-NPC-Editor",
        "editor.py"
    ]
    
    subprocess.check_call(cmd)
    print("Build complete.")
    print(f"Executable created at: {os.path.abspath('dist/SMBX-NPC-Editor.exe')}")

if __name__ == "__main__":
    try:
        # Check if pyinstaller is installed
        try:
            subprocess.check_call(["pyinstaller", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("PyInstaller not found. Installing dependencies...")
            install_requirements()

        build_exe()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
