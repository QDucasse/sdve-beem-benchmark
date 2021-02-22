import os
import csv
import glob

# [X] Find the number of transient values
# [X] Find the number of non transient values
# [X] Find the number of processes
# [X] Find the number of ops in GuardBlock (mean and max)
# [X] Find the number of ops in Effect (mean and max)

def process_files():
    '''
    Run the process over all files and outputs a csv file
    '''
    sdve_files = glob.glob("**/*.sdve", recursive=True)
    res_dicts = []
    for file in sdve_files:
        res_dicts.append(process_file(file))
    # Write to csv file
    col_name=["Name",
              "# Temporary var",
              "# Non-temporary var",
              "# Processes",
              "Max # op in Guard",
              "Mean # op in Guard",
              "Max # simultaneous alive vars in Guard",
              "Max # op in Effect",
              "Mean # op in Effect",
              "Max # simultaneous alive vars in Effect"
    ]
    with open("stats.csv", 'w') as csvFile:
        wr = csv.DictWriter(csvFile, fieldnames=col_name)
        wr.writeheader()
        for ele in res_dicts:
            wr.writerow(ele)


def process_file(sdve_filepath):
    '''
    Output a dictionary with stats from a file path
    '''
    max_ops_in_guard     = 0
    mean_ops_in_guard    = 0
    max_ops_in_effect    = 0
    mean_ops_in_effect   = 0
    # Preprocess
    file_name, content = preprocess_file(sdve_filepath)
    print("Getting stats for: " + file_name)
    # Separates regions: variable declarations and each process
    var_declarations, processes = extract_decl_and_proc(content)
    # Process the var declarations to get the number of transient and non-transient variables
    transient_number, non_transient_number = process_variable_declarations(var_declarations)
    # Get the number of processes
    process_number = len(processes)
    # Get stats on guards and effects
    guard_max, guard_mean, guard_max_alive, effect_max, effect_mean, effect_max_alive = process_guards_effects(processes)
    # Structure the results in a dict
    res_dict = {
        "Name":                file_name,
        "# Transient var":     transient_number,
        "# Non-transient var": non_transient_number,
        "# Processes": process_number,
        "Max # op in Guard":   guard_max,
        "Mean # op in Guard":  round(guard_mean,2),
        "Max # simultaneous alive vars in Guard": guard_max_alive,
        "Max # op in Effect":  effect_max,
        "Mean # op in Effect": round(effect_mean,2),
        "Max # simultaneous alive vars in Effect": effect_max_alive,
    }
    return res_dict

def preprocess_file(filename):
    '''
    From a path, gets the name of the file and extracts the content
    '''
    sdve_file_name = filename.split("/")[1][:-5]
    with open(filename) as f:
        content = f.readlines()

    content = [line.strip() for line in content] # Remove trailing and leading spaces
    content = [line for line in content if line] # Remove empty strings
    return sdve_file_name, content

def extract_decl_and_proc(content):
    '''
    Extract the different regions from the contents of the file
    '''
    # Split the content on every "process" encouter
    process_indexes = (i for i,v in enumerate(content) if "process" in v)
    old_proc_ind  = 0
    next_proc_ind = next(process_indexes, 0)

    # Variable declarations
    var_decl = content[:next_proc_ind]

    # Processes
    processes = []
    # Step 0
    old_proc_ind = next_proc_ind
    next_proc_ind = next(process_indexes, 0)
    # Run through all the others
    while(next_proc_ind != 0):
        processes.append(content[old_proc_ind:next_proc_ind])
        old_proc_ind = next_proc_ind
        next_proc_ind = next(process_indexes, 0)
    return var_decl, processes

def process_variable_declarations(var_decl_list):
    '''
    Outputs the number of transient variables declared as well as the number of
    non-transient variables declared.
    '''
    transient_var = [var for var in var_decl_list if "transient" in var]
    return len(transient_var), len(var_decl_list) - len(transient_var)

def process_guards_effects(processes):
    '''
    Outputs stats from the guards and effects
    '''
    guard_max        = 0
    guard_mean       = 0
    guard_max_alive  = 0
    effect_max       = 0
    effect_mean      = 0
    effect_max_alive = 0
    for i,process in enumerate(processes):
        op_guard, op_effect, alive_guard, alive_effect = process_guard_effect(process)
        # Guard stats
        guard_max  = max(guard_max, op_guard)
        guard_mean += ((op_guard - guard_mean) / (i + 1))
        guard_max_alive = max(guard_max_alive, alive_guard)
        # Effect stats
        effect_max = max(effect_max, op_effect)
        effect_mean += ((op_effect - effect_mean) / (i + 1))
        effect_max_alive = max(effect_max_alive, alive_effect)
    return guard_max, guard_mean, guard_max_alive, effect_max, effect_mean, effect_max_alive

def process_guard_effect(process):
    '''
    Get the number of operation in the guard and effect of a given process
    '''
    guard_cond_index = next(i for i,v in enumerate(process) if "guardCondition" in v)
    guard_block = process[2:guard_cond_index]
    effect_block = process[guard_cond_index+2:]
    # Compute lengths
    len_guard_cond = len(guard_block)
    len_effect = len(effect_block)
    # Find max number of simultaneous alive variables
    # print("\n\n----\nGuard\n----\n\n")
    max_alive_vars_guard = determine_alive_vars(guard_block)
    # print("\n\n----\nEffect\n----\n\n")
    max_alive_vars_effect = determine_alive_vars(effect_block)
    return len_guard_cond, len_effect, max_alive_vars_guard, max_alive_vars_effect

def determine_alive_vars(block):
    '''
    Determine the number of simultaneous alive variables in a block.
    '''
    # print(block)
    max_alive_vars = 0
    alive_vars = []
    for line in block:
        # print("Alive vars: " + str(alive_vars))
        var, expr = line.split(" = ")
        # Process left hand
        if var.startswith("t_") and not(var in alive_vars):
            # print("Left hand: " + var)
            alive_vars.append(var)
            max_alive_vars = max(max_alive_vars, len(alive_vars))
        # Process right hand
        # Remove the variables in the right side (dead)
        # print("Right hand: " + expr)
        alive_vars = [var for var in alive_vars if not(var in expr)]
        max_alive_vars = max(max_alive_vars, len(alive_vars))
    return max_alive_vars

if __name__ == "__main__":
    # process_file("anderson/anderson.1.prop2.sdve")
    process_files()
