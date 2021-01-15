import subprocess
import glob

if __name__ == "__main__":
    sdve_files = glob.glob("**/*.sdve", recursive=True)
    for file in sdve_files:
        subprocess.call("sdvu " + file, shell=True)
