import os
import glob

def process_files():
    sdve_files = glob.glob("**/*.sdve", recursive=True)
    sdve_files = [sdve_file for sdve_file in sdve_files if "prop" in sdve_file]

    for sdve_file in sdve_files:
        print(sdve_file)
        lines = open(sdve_file, 'r').readlines()
        if "//" in lines[-2]:
            continue
        else:
            new_minus2 = "      // " + lines[-2].lstrip()
            new_minus1 = "      // " + lines[-1].lstrip()
            lines[-2] = new_minus2
            lines[-1] = new_minus1
            open(sdve_file, 'w').writelines(lines)

if __name__ == "__main__":
    # process_file("anderson/anderson.1.prop2.sdve")
    process_files()
