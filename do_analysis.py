#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#
#
# This is for a 4-core machine!

import argparse, subprocess, Bio, os, sys, shutil
from Bio import SeqIO

# old function
#def execute_subprocess(comment, bash_command):
#    print("\n" + comment, bash_command)
#    process = subprocess.Popen(bash_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
#    output, error = process.communicate()
#    process_status = process.wait()
#    if output.decode('utf-8') != '':
#        print("Output: " + str(output))
#    if error.decode('UTF-8') != '':
#        print("Error: " + str(error))
       
def execute_subprocess(comment, bash_command, env_variables={}, working_directory='.'):
    print("\n" + comment, bash_command, "Environment variables:", env_variables, "Working directory:", working_directory)
    # Maybe replace with convienience function "subprocess.run"?
    process = subprocess.Popen(bash_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=working_directory, env=env_variables)
    output, error = process.communicate()
    process_status = process.wait()
    output = output.decode('utf-8')
    error = error.decode('utf-8')
    if output != '':
        print('Output: {0}'.format(output))
    if error != '':
        print('Error: {0}'.format(error))
    return output, error

def run():
    records = list(SeqIO.parse(sys.argv[1], "fasta"))
    print("The fasta file contains " + str(len(records)) + " sequences.")

    FASTA = sys.argv[1]
    BASENAME = os.path.splitext(FASTA)[0]
    FASTA_ALIGNED = BASENAME+".aln" 
    FASTA_ALIGNED_CODED = BASENAME+"_encoded.fasta" 
    PHYLIP_ALIGNED_CODED = BASENAME+"_encoded.phy" 
    PHYLIP_ALIGNED_DECODED = BASENAME+"_decoded.tree" 

    #Commented out because passing the env variables to the script does not work
    
    environment_variables = dict(os.environ)   # Make a copy of the current environment
    environment_variables['MAX_N_PID_4_TCOFFEE'] = '5000000'
    
    # t_coffee vegfrs.fasta -outfile vegfrs.aln -output=fasta_aln -mode mcoffee -multi_core=4
    execute_subprocess(
        "Generating multiple sequence alignment with the following command:",
        "t_coffee " + FASTA + " -outfile " + FASTA_ALIGNED + " -output=fasta_aln -mode mcoffee -multi_core=4", environment_variables)

    # t_coffee -other_pg seq_reformat -in vegfrs.aln -output code_name > code_names.list
    execute_subprocess(
        "Converting fasta descriptions part 1 (creating code list) with t_coffee using the following command:",
        "t_coffee -other_pg seq_reformat -in " + FASTA_ALIGNED + " -output code_name > code_names.list")

    # t_coffee -other_pg seq_reformat -code code_names.list -in vegfrs.aln > vegfrs_encoded.fasta
    execute_subprocess(
        "Converting fasta descriptions part 2 (replacing fasta descriptions with codes) with t_cofeee using the following command:",
        "t_coffee -other_pg seq_reformat -code code_names.list -in " + FASTA_ALIGNED + " > " + FASTA_ALIGNED_CODED)

    # t_coffee -other_pg seq_reformat -in vegfrs_encoded.fasta -output phylip_aln > vegfrs_encoded.phy
    execute_subprocess(
        "Convert into phylip using the following command:",
        "t_coffee -other_pg seq_reformat -in " + FASTA_ALIGNED_CODED + " -output phylip_aln > " + PHYLIP_ALIGNED_CODED)

    # Detect whether parallel bootstrapping should be performed
    mpirun_path = shutil.which('mpirun')
    phymlmpi_path = shutil.which('phyml-mpi')
    
    # mpirun -n 4 phyml-mpi -i vegfrs_encoded.phy --quiet -d aa -b -1
    if mpirun_path != '' and phymlmpi_path != '':
        phylo_command = "mpirun -n 4 phyml-mpi -i " + PHYLIP_ALIGNED_CODED +  " --quiet -d aa -b -1"
    else:
        phylo_command = "phyml -i " + PHYLIP_ALIGNED_CODED +  " --quiet -d aa -b -1"

    # The gene tree building is actually never used since the species tree is used for the tree drawing.
    # We anyway calculate it to be able to compare gene and species trees.
    execute_subprocess(
        "Make tree with the following command:",
        phylo_command)

    # phyml adds or doesn't add the .txt extension to the output file (depending on the version) and we need to check for this!
    phyml_output_file = PHYLIP_ALIGNED_CODED + "_phyml_tree"
    if os.path.isfile(phyml_output_file):
        os.rename(phyml_output_file, phyml_output_file + ".txt")
    
    # t_coffee -other_pg seq_reformat -decode code_names.list -in vegfrs_encoded.phy_phyml_tree.txt > vegfrs_decoded.tree
    execute_subprocess(
        "Decoding tree file file into human-readable format using the following command:",
        "t_coffee -other_pg seq_reformat -decode code_names.list -in " + phyml_output_file + ".txt > " + PHYLIP_ALIGNED_DECODED)

if __name__ == '__main__':
    run()
