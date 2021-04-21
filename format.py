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
    # sdve_files = [sdve_file for sdve_file in sdve_files if not("prop" in sdve_file) and "telephony." in sdve_file]

    for sdve_file in sdve_files:
        reorder_global_declarations(sdve_file)


def reorder_global_declarations(sdve_file):
    with open(sdve_file) as f:
        content = f.readlines()
        content = [line.strip() for line in content] # Remove trailing and leading spaces
        content = [line for line in content if line] # Remove empty strings
    # Split the content on every "process" encouter
    process_indexes = (i for i,v in enumerate(content) if "process" in v)
    next_proc_ind = next(process_indexes, 0)
    # Global declarations
    globs = content[:next_proc_ind]
    ints   = [decl for decl in globs if decl.split(" ")[0] == "int"]
    states = [decl for decl in globs if decl.split(" ")[0] == "state"]
    bytes  = [decl for decl in globs if decl.split(" ")[0] == "byte"]
    bools  = [decl for decl in globs if decl.split(" ")[0] == "bool"]

    globs = ints + states + bytes + bools

    with open(sdve_file, "r") as f:
        content = f.readlines()

    with open(sdve_file, "w") as f:
        f.write("\n".join(globs) + "\n" + "".join(content[len(globs):]))

if __name__ == "__main__":
    # print(determine_cfg_size("adding/adding.1.sdve"))
    process_files()
    # reorder_global_declarations("anderson/anderson.1.sdve")
