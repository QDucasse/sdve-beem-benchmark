import os
import glob
import subprocess

error_arr = ["blocks", "driving_phils", "telephony", "mcs"]
error_shl = ["synapse"]
error_biz = ["loyd"]

error_sim = ["bridge", "cambridge", "collision", "extinction",
             "frogs", "hanoi", "lifts", "needham", "peterson",
             "protocols", "rushhour", "sokoban"]

def process_files():
    sdve_files = glob.glob("**/*.sdve", recursive=True)
    sdve_files = [sdve_file for sdve_file in sdve_files if not("prop" in sdve_file) and "telephony." in sdve_file]

    for sdve_file in sdve_files:
        for ncores in range(1,10):
            print(sdve_file)
            subprocess.check_output(["python", "../sdvs/sdvs/sdvs.py",
                                     "-s", sdve_file,
                                      "--ncores", str(ncores),
                                      "--cfgsize", str(determine_cfg_size(sdve_file)),
                                      "--cfg", str(0),
                                      "--outputfile", "exec_stats.csv"
                              ])

def determine_cfg_size(sdve_file):
    with open(sdve_file) as f:
        content = f.readlines()
        content = [line.strip() for line in content] # Remove trailing and leading spaces
        content = [line for line in content if line] # Remove empty strings

    cfg_size = 0
    i = 0
    while not(content[i].startswith("process")):
        if content[i].startswith("bool"):
            cfg_size += 8
        elif content[i].startswith("byte"):
            cfg_size += 8
        elif content[i].startswith("state"):
            cfg_size += 16
        elif content[i].startswith("int"):
            cfg_size += 32
        i+=1
    return cfg_size


if __name__ == "__main__":
    # print(determine_cfg_size("adding/adding.1.sdve"))
    process_files()
