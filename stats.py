import os
import csv
import glob
import subprocess
# ========================================= #
#               STATIC STATS                #
# ========================================= #

# [X] Find the number of transient values
# [X] Find the number of non transient values
# [X] Find the number of processes
# [X] Find the number of ops in GuardBlock (mean and max)
# [X] Find the number of ops in Effect (mean and max)

def shouldBeProcessed(filename):
    error_arr = ["blocks", "driving_phils", "telephony", "mcs"]
    error_shl = ["synapse"]
    error_biz = ["loyd"]
    for word in error_arr + error_biz + error_shl:
        if word in filename:
            return False
    return True

def process_files():
    '''
    Run the process over all files and outputs a csv file
    '''
    sdve_files = glob.glob("**/*.sdve", recursive=True)
    sdve_files = [sdve_file for sdve_file in sdve_files if shouldBeProcessed(sdve_file)]
    res_dicts = []
    for file in sdve_files:
        res_dicts.append(process_file(file))
    # Write to csv file
    col_name=["Name",
              "Number of Temporaries",
              "Number of Globals",
              "Number of Guard/Actions",
              "Max number of assignments in Guard",
              "Mean number of assignments in Guard",
              "Max number simultaneous alive temporaries in Guard",
              "Max number of assignments in Effect",
              "Mean number of assignments in Effect",
              "Max number simultaneous alive temporaries in Effect",
              "Number of instructions",
              "Binary size"
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
    globs, processes = extract_decl_and_proc(content)
    # Process the var declarations to get the number of temporary and global variables
    nb_temp, nb_glob = process_variables(globs, content)
    # Get the number of processes
    nb_guard_action = len(processes)
    # Get stats on guards and effects
    guard_max, guard_mean, guard_max_alive, effect_max, effect_mean, effect_max_alive = process_guards_effects(processes)
    # Compile the file
    nb_instruction, binary_size = compile_file(sdve_filepath)
    # Structure the results in a dict
    res_dict = {
      "Name":                                                file_name,
      "Number of Temporaries":                               nb_temp,
      "Number of Globals":                                   nb_glob,
      "Number of Guard/Actions":                             nb_guard_action,
      "Max number of assignments in Guard":                  guard_max,
      "Mean number of assignments in Guard":                 round(guard_mean,2),
      "Max number simultaneous alive temporaries in Guard":  guard_max_alive,
      "Max number of assignments in Effect":                 effect_max,
      "Mean number of assignments in Effect":                round(effect_mean,2),
      "Max number simultaneous alive temporaries in Effect": effect_max_alive,
      "Number of instructions":                              nb_instruction,
      "Binary size":                                         binary_size
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

    # Global declarations
    globs = content[:next_proc_ind]

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
    return globs, processes

def process_variables(globals, content):
    '''
    Outputs the number of transient variables declared as well as the number of
    non-transient variables declared.
    '''
    nb_glob = len(globals)
    nb_temp = content.count("temp")
    return nb_temp, nb_glob


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
    max_alive_vars_guard  = determine_alive_vars(guard_block)  # in guard
    max_alive_vars_effect = determine_alive_vars(effect_block) # in effect
    return len_guard_cond, len_effect, max_alive_vars_guard, max_alive_vars_effect

def determine_alive_vars(block):
    '''
    Determine the number of simultaneous alive variables in a block.
    '''
    max_alive_vars = 0
    alive_vars = []
    for line in block:
        var, expr = line.split(" = ")
        # Process left hand
        if var.startswith("temp "):
            var_name = var.split(" ")[2]
            var_type = var.split(" ")[1]
            if not(var_name in alive_vars):
                alive_vars.append(var_name)
                max_alive_vars = max(max_alive_vars, len(alive_vars))
        # Process right hand
        # Remove the variables in the right side (dead)
        alive_vars = [temp_var for temp_var in alive_vars if not(temp_var in expr)]
        max_alive_vars = max(max_alive_vars, len(alive_vars))
    return max_alive_vars

def compile_file(file_name):
    '''
    Compile a given file and gather stats.
    '''
    cropped_file_name = file_name.split("/")[1][:-5]
    output_file = "bin/" + cropped_file_name + ".out"
    output = subprocess.check_output(["./sdvc", "-v", "-c", file_name,"-o", output_file])
    instruction_number = int(output.decode().split(" ")[-1].strip())
    binary_size = os.stat(output_file).st_size
    return instruction_number, binary_size

# ========================================= #
#             SIMULATION STATS              #
# ========================================= #

error_arr = ["blocks", "driving_phils", "telephony", "mcs"]
error_shl = ["synapse"]
error_biz = ["loyd"]
error_neg = ["cambridge", "firewire_link"]
error_sim = ["collision", "extinction", "lifts", "needham", "protocols"]
error_mod = list(set(error_arr + error_shl + error_biz + error_sim + error_neg))

small_cfg_models = [
"phils.1",
"firewire_tree.1",
"needham.1",
"pouring.1",
"public_subscribe.1",
"phils.2",
"fischer.1",
"loyd.1",
"phils.3",
"rushhour.1",
"bakery.2",
"telephony.1",
"lup.1",
"mcs.2",
"anderson.2",
"bakery.1",
"firewire_link.1",
"elevator2.1",
"rushhour.2",
"msmie.1",
"protocols.1",
"firewire_tree.2",
"rether.1",
"lifts.1",
"lifts.2",
"reader_writer.1",
"gear.1",
"protocols.3",
"elevator.2",
"bridge.1",
"cyclic_scheduler.2",
"reader_writer.2",
"cyclic_scheduler.1",
"leader_filters.1",
"frogs.1",
"collision.1",
"krebs.1",
"hanoi.1",
"iprotocol.1",
"blocks.2",
"adding.1",
"plc.1",
"sorter.2",
"mcs.1",
"elevator.1",
"extinction.1",
"production_cell.2",
"rether.2",
"extinction.2",
"pgm_protocol.1",
"protocols.2",
"cambridge.1",
"peterson.1",
"bopdp.1",
"collision.2",
"lann.2",
"lamport_nonatomic.2",
"leader_election.1",
"production_cell.1",
"driving_phils.1",
"cambridge.2",
"mcs.4",
"gear.2",
"pgm_protocol.2",
"cambridge.3",
"frogs.2",
"lann.1",
"brp.1",
"szymanski.1",
"lamport_nonatomic.1",
"sorter.1",
"fischer.2",
"schedule_world.1",
"firewire_link.4",
"bopdp.2",
"elevator_planning.1",
"leader_election.2",
"brp.2",
"lamport.1",
"leader_filters.2",
"anderson.4",
"iprotocol.2",
"szymanski.2",
"peg_solitaire.1",
"bakery.3",
"driving_phils.2",
"exit.2",
"lamport_nonatomic.3",
"lamport.3",
"at.1",
"pgm_protocol.4",
"at.2",
"leader_filters.4",
"needham.2",
"pouring.2",
"telephony.2",
"elevator_planning.3",
"firewire_link.2",
"cambridge.4",
"krebs.2",
"peg_solitaire.5",
"firewire_tree.3",
"leader_filters.3",
"sokoban.1",
"bridge.2",
"leader_election.3"
]

def process_exec_stats():
    sdve_files = glob.glob("**/*.sdve", recursive=True)
    # Remove prop models
    sdve_files = [sdve_file for sdve_file in sdve_files if not("prop" in sdve_file)]
    # Remove error models
    sdve_files = [sdve_file for sdve_file in sdve_files if not(any(model_name in sdve_file for model_name in error_mod))]
    # Only take in account the models with less than 100k configurations
    sdve_files = [sdve_file for sdve_file in sdve_files if any(model_name in sdve_file for model_name in small_cfg_models)]
    for sdve_file in sdve_files:
        # Launching simulation
        exec_stat(sdve_file)

def exec_stat(sdve_file):
    for ncores in [1,2,4,8,16]:
        print("{}: Starting simulation with {} core(s)".format(sdve_file, ncores))
        subprocess.run(["python", "../sdvs/sdvs/sdvs.py",
                                 "-s", sdve_file,
                                  "--ncores", str(ncores),
                                  "--outputfile", "exec_stats.csv"
                          ])
        print("Result written in the output file.")

if __name__ == "__main__":
    exec_stat("firewire_tree/firewire_tree.1.sdve")
    # process_exec_stats()
