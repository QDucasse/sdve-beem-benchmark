import os
import glob

def process_files(order_func):
    sdve_files = glob.glob("**/*.sdve", recursive=True)
    # sdve_files = [sdve_file for sdve_file in sdve_files if not("prop" in sdve_file) and "telephony." in sdve_file]

    for sdve_file in sdve_files:
        order_func(sdve_file)


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


def generate_initial_config(sdve_file):
    with open(sdve_file) as f:
        content = f.readlines()
        content = [line.strip() for line in content] # Remove trailing and leading spaces
        content = [line for line in content if line] # Remove empty strings
    # Split the content on every "process" encouter
    process_indexes = (i for i,v in enumerate(content) if "process" in v)
    next_proc_ind = next(process_indexes, 0)
    # Global declarations
    config_values = []
    globs = content[:next_proc_ind]
    for glob_decl in globs:
        type = glob_decl.split(" ")[0]
        value = glob_decl.split("= ")[1][:-1]
        name = glob_decl.split(" ")[1]
        is_array = name.endswith("]")
        if type == "int":
            if is_array:
                config_values += proc_config_array(value, 8)
            else:
                config_values.append("{0:0{1}X}".format(int(value), 8))
        elif type == "state":
            if is_array:
                config_values += proc_config_array(value, 4)
            else:
                config_values.append("{0:0{1}X}".format(int(value), 4))
        elif type == "byte" or type == "bool":
            if is_array:
                config_values += proc_config_array(value, 2)
            else:
                config_values.append("{0:0{1}X}".format(int(value), 2))

    config_values.reverse()
    initial_config = "".join(config_values)

    with open(sdve_file[:-5]+".cfg", "w") as f:
        f.write(initial_config)

def proc_config_array(values, type_size):
    values = values[2:-1].split(", ")  # Remove { }
    values = ["{0:0{1}X}".format(int(value), type_size) for value in values]
    return values


if __name__ == "__main__":
    process_files(generate_initial_config)
    # generate_initial_config("adding/adding.6.sdve")
