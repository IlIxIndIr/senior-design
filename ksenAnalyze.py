"""Python script to adjust Comet assembly plate configuration and run MCNP via batch file."""
import math as m
import numpy as np
import pandas as pd
import os
from subprocess import call
import mmap
import matplotlib.pyplot as plt

# define relative file paths to this script from the absolute file paths
mcnp_path = os.path.relpath('../MY_MCNP/MCNP_CODE/bin/mcnp6.exe', os.getcwd())
mcnp_sim_path = os.path.relpath('.', os.getcwd())
input_path = os.path.join(mcnp_sim_path, os.path.relpath('MANE4390/inputs/'))
output_path = os.path.join(mcnp_sim_path, os.path.relpath('MANE4390/outputs/'))
run = os.path.join(mcnp_sim_path, os.path.relpath('run.bat'))

# define global empty value arrays
low_eb, high_eb, sen_vals, sen_unc = np.array([]), np.array([]), np.array([]), np.array([])

# find list of files to analyze
for root, dirs, files in os.walk(output_path):
    for file in files:
        if file[0:3] == 'out':
            # load in sensitivity data from file
            # sen_data = np.genfromtxt(os.path.join(output_path, file), skip_header=20, usecols=4)
            out_file = os.path.join(output_path, file)
            with open(out_file, 'rb', 0) as mm, \
                    mmap.mmap(mm.fileno(), 0, access=mmap.ACCESS_READ) as s:
                if s.find(b'26056.00c total') != -1:
                    # headers: print(s[s.find(b'6012.00c total'):s.find(b'rel. unc.')+15])
                    # print(s[(s.find(b'rel. unc.')+15):(s.find(b'rel. unc.')+2830)])
                    sen_str = s[(s.find(b'26056.00c total')+86):(s.find(b'26056.00c total')+16214)].decode("utf-8")

                    # write data excerpt to file and re-import as a numpy array
                    with open('temp.txt', 'w') as f:
                        f.write(sen_str)
                    sen_array = np.genfromtxt('temp.txt')
                    os.remove('temp.txt')

                    # convert array into a DataFrame for plotting
                    sen_data = pd.DataFrame(data=sen_array, columns=['low_eb', 'high_eb', 'sen_vals', 'sen_unc'])

                    # define empty lethargy and sensitivity per lethargy arrays
                    lethargy = np.log(np.divide(sen_data['high_eb'], sen_data['low_eb']))
                    sen_data['sen_leth'] = np.divide(sen_data['sen_vals'], lethargy)

                    # plot sensitivity profile
                    fig, ax = plt.subplots()
                    e = np.insert(np.array(sen_data['high_eb']), 0, sen_data['low_eb'][0])
                    spl = np.insert(np.array(sen_data['sen_leth']), 0, sen_data['sen_leth'][0])
                    ax.step(e, spl, where='pre')
                    
                    # format plot
                    # set axis labels & title
                    ax.set_title('26056.00c total (1p8 U6)')
                    ax.set_xlabel('Energy [MeV]', labelpad=20, weight='bold', size=12)
                    ax.set_ylabel('$S_{k, \sigma}$ (Sensitivity per Unit Lethargy)',
                                  labelpad=20, weight='bold', size=12)

                    # set x-axis to log scale & axis limits
                    ax.set_xscale('log')
                    plt.xlim(sen_data['low_eb'].min(), sen_data['high_eb'].max())

                    # set the grid on & ticks
                    ax.grid('on', linestyle='--', alpha=.3, linewidth=.5)
                    ax.tick_params(bottom=True, top=True, left=True, right=True)
                    ax.tick_params(axis="x", direction="in")
                    ax.tick_params(axis="y", direction="in")

                    # define error bars
                    mid_e = (sen_data['low_eb'] + sen_data['high_eb'])/2
                    sen_leth_unc = np.multiply(sen_data['sen_leth'], sen_data['sen_unc'])
                    plt.errorbar(mid_e, sen_data['sen_leth'], yerr=sen_leth_unc, fmt='none', color='black')

                    plt.show()
                    plt.savefig("KSEN_plot.png", bbox_inches='tight', dpi=1200)
