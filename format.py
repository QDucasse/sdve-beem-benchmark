# The different methods in this file consists of passes over sdve files

import os
import glob
from shutil import copyfile

# ===============================
#       Files processing
# ===============================

def process_files(order_func):
    '''
    Performs a pass on all sdve files.
    '''

    if (not(DEBUG)):
        sdve_files = glob.glob("**/*.sdve", recursive=True)
        sdve_files = [sdve_file for sdve_file in sdve_files if not("test" in sdve_file)]
    else:
        sdve_files = glob.glob("running_test.sdve", recursive=True)


    for sdve_file in sdve_files:
        print(sdve_file + ": Processing " + str(order_func.__name__))
        order_func(sdve_file)


def preprocessed_content(sdve_file):
    '''
    Preprocess the file by removing the empty lines and formatting spaces.
    '''
    with open(sdve_file) as f:
        content = f.readlines()
        content = [line.strip() for line in content] # Remove trailing and leading spaces
        content = [line for line in content if line] # Remove empty strings
    return content

def base_content(sdve_file):
    with open(sdve_file) as f:
        content = f.readlines()
    return content

# =================================
#       Remove system async
# =================================

def remove_system_async(sdve_file):
    '''
    Remove the last line system async.
    '''
    content = base_content(sdve_file)
    if "system async" in content[-1]:
        with open(sdve_file, "w") as f:
            f.write("".join(content[:-1]))

# =================================
#       Remove system async
# =================================

def change_tab_to_space(sdve_file):
    '''
    Remove the last line system async.
    '''
    content = base_content(sdve_file)
    new_content = []
    for line in content:
        line = line.replace("\t", "  ")
        new_content.append(line)

    with open(sdve_file, "w") as f:
        f.write("".join(new_content))

# =================================
#    Temporaries Propagation
# =================================

def propagate_temporaries(sdve_file):
    '''
    Bring the temporaries inside the guard they are defined in.
    '''
    content = base_content(sdve_file)
    temp_types = {}
    # Get the first proc index
    process_indexes = (i for i,v in enumerate(content) if "process" in v)
    next_proc_ind = next(process_indexes, 0)

    temp_indexes = (i for i,v in enumerate(content) if "temp" in v)
    next_temp_ind = next(temp_indexes, 0)
    # Declarations and temporary declarations
    decls = content[:next_proc_ind]
    glob_decls = decls[:next_temp_ind]
    temp_decls = decls[next_temp_ind:next_proc_ind]
    # Extract types
    for temp in temp_decls:
        temp_name = temp.split(" ")[2]
        temp_type = temp.split(" ")[1]
        temp_types[temp_name] = temp_type
    # Rewrite declarations
    new_lines = []
    for line in content[next_proc_ind:]:
        if line.strip().startswith("t_"):
            # Temporary name
            temp_name = line.strip().split(" ")[0]
            line = line.replace(temp_name, "temp " + temp_types[temp_name] + " " + temp_name)
        new_lines.append(line)

    # Rewrite the file
    with open(sdve_file, "w") as f:
        f.write("".join(glob_decls) + "\n" + "".join(new_lines))

# ====================================
#          AND OR Syntax
# ====================================

def change_and_or(sdve_file):
    '''
    Change | to 'or' and & to 'and'.
    '''
    content = base_content(sdve_file)
    new_content = []
    for line in content:
        if (' | ' in line):
            line = line.replace(' | ', ' or ')
        if (' & ' in line):
            line = line.replace(' & ', ' and ')
        new_content.append(line)

    # Rewrite the file
    with open(sdve_file, "w") as f:
        f.write("".join(new_content))

# ====================================
#        Change Array syntax
# ====================================

def change_array_syntax(sdve_file):
    '''
    Change byte[3] Slot = {1, 0, 0} to byte Slot[3] = {1, 0, 0}.
    '''
    content = base_content(sdve_file)
    # Get the first proc index
    process_indexes = (i for i,v in enumerate(content) if "process" in v)
    next_proc_ind = next(process_indexes, 0)
    decls = content[:next_proc_ind]

    new_decls = []
    for decl in decls:
        if '[' in decl:
            type = decl.split('[')[0]
            name = decl.split(' ')[1]
            length = decl.count(',') + 1
            array = decl.split('= ')[1]
            decl = type + ' ' + name + '[' + str(length) + ']' + ' = ' + array
        new_decls.append(decl)

    # Rewrite the file
    with open(sdve_file, 'w') as f:
        f.write("".join(new_decls) + "".join(content[next_proc_ind:]))


# ====================================
#       Constant Propagation
# ====================================

def propagate_constants(sdve_file):
    '''
    Remove the const keyword and propagate the different constants.
    '''
    content = base_content(sdve_file)
    # Get the first proc index
    process_indexes = (i for i,v in enumerate(content) if "process" in v)
    next_proc_ind = next(process_indexes, 0)
    decls = content[:next_proc_ind]

    constant_dict = {}
    new_decls = []
    for decl in decls:
        if 'const' in decl:
            name = decl.split(' ')[2]
            value = decl.strip().split('= ')[1][:-1]
            decl = ''
            constant_dict[name] = value

        for constant in constant_dict.keys():
            if constant in decl:
                decl = decl.replace(constant, constant_dict[constant])

        new_decls.append(decl)

    new_decls = [decl for decl in new_decls if decl]
    new_decls_evaluated = []
    for decl in new_decls[:-1]:
        if not('[' in decl):
            decl = decl.split(" = ")[0] + " = " + str(eval(decl.strip().split(" = ")[1][:-1])) + ";\n"
        new_decls_evaluated.append(decl)

    new_content = []
    for line in content[next_proc_ind:]:
        for constant in constant_dict.keys():
            if constant in line:
                line = line.replace(constant, constant_dict[constant])
        new_content.append(line)

    # Rewrite the file
    with open(sdve_file, 'w') as f:
        f.write("".join(new_decls_evaluated) + "".join(new_content))

# ====================================
#    Comment Accepting Conditions
# ====================================

def comment_accepting_conditions(sdve_file):
    '''
    Comment the line 'accepting condition' and the following ones.
    '''
    content = base_content(sdve_file)

    accepting_conditions_indexes = (i for i,v in enumerate(content) if "accepting conditions" in v)
    acc_cond_ind = next(accepting_conditions_indexes, 0)

    new_content = content[:acc_cond_ind]

    for line in content[acc_cond_ind:]:
        line = "// " + line
        new_content.append(line)

    with open(sdve_file, 'w') as f:
        f.write("".join(new_content))

# ====================================
#    Global Declarations Reordering
# ====================================

def reorder_global_declarations(sdve_file):
    '''
    Reorders the global declarations with
    int -> state -> byte -> bool
    '''
    content = preprocessed_content(sdve_file)
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
    # Reopen a clean copy to get the tabulated end
    with open(sdve_file, "r") as f:
        content = f.readlines()
    # Write the global declarations then the rest of the file
    with open(sdve_file, "w") as f:
        f.write("\n".join(globs) + "\n\n" + "".join(content[len(globs):]))

# ===============================
#    Initial Config Generation
# ===============================

def generate_initial_config(sdve_file):
    '''
    Generate the .cfg file with the initial config.
    '''
    content = preprocessed_content(sdve_file)
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
                config_values.append(proc_config_array(value, 8))
            else:
                config_values.append("{0:0{1}X}".format(int(value), 8))
        elif type == "state":
            config_values.append("{0:0{1}X}".format(int(value), 4))
        elif type == "byte" or type == "bool":
            if is_array:
                config_values.append(proc_config_array(value, 2))
            else:
                config_values.append("{0:0{1}X}".format(int(value), 2))

    config_values.reverse()
    config_values = list(flatten(config_values))
    initial_config = "".join(config_values)

    with open(sdve_file[:-5]+".cfg", "w") as f:
        f.write(initial_config)

def proc_config_array(values, type_size):
    values = values[1:-1].split(", ")  # Remove { }
    values = ["{0:0{1}X}".format(int(value), type_size) for value in values]
    return values

def flatten(l):
    for el in l:
        if isinstance(el, list) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


if __name__ == "__main__":
    DEBUG = False
    if DEBUG:
        copyfile("test.sdve", "running_test.sdve")
    # process_files(remove_system_async)
    # process_files(change_tab_to_space)
    # process_files(propagate_temporaries)
    # process_files(change_array_syntax)
    # process_files(propagate_constants)
    # process_files(change_and_or)
    # process_files(comment_accepting_conditions)
    # process_files(reorder_global_declarations)
    process_files(generate_initial_config)
    # generate_initial_config("firewire_tree/firewire_tree.1.sdve")
    # generate_initial_config("adding/adding.6.sdve")
