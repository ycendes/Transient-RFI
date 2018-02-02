#!/bin/python

# This script is an alert script for an observer to use to check whether a measurement set has a potential transient in the data stream, as described in "RFI Flagging Implications for Short Duration Transients" by Cendes et al. (submitted to Astronomy & Computing).  This script was written for a pre-processed LOFAR data set, and will need to be updated accordingly for a different telescope or pre-processed data.  "mod.rfis" is the modified RFI flagging strategy developed for transients, which is also available in this repository.

# Last updated Jan 31, 2018. Contact: yvette.cendesatgmail.com

import os
import math
import random
import sys
from casacore import tables
from pyrap.tables import table
import numpy as np
import time
import pyrap.images as pim
import pyrap.tables as pt
import numpy.ma
from joblib import Parallel, delayed
import multiprocessing

#first, getting our measurement set ready and running AOFlagger and modified strategy on the data set

msname='full-default.MS.dppp'
msname2='full-mod.MS.dppp'
os.system('cp -rf full.MS.dppp full-default.MS.dppp/')
os.system('cp -rf full.MS.dppp full-mod.MS.dppp')
os.system('aoflagger '+ msname+'> log-default.log')
os.system('aoflagger -strategy mod.rfis'+ msname2+'> log-mod.log')

#here we are obtaining the average percentage flagged for both strategies based on information extrated from the AOFlagger logs
        
fhand = open('log-default.log')
print(fhand)
all_values = []
for line in fhand:
    line = line.rstrip()
    if line.startswith('Channel') : 
        values=line.split()
        chan1 = values[3:-1]
        newvalues = [x[:-1] for x in chan1]
        newvalues = [float(i) for i in newvalues]
        all_values.append(newvalues)
    if not line.startswith('From:') :
        sys.exit('Error in log file- no percentaged flagged by channel')

default_avg = np.mean(all_values[0])+np.mean(all_values[1])/len(all_values[0]+all_values[1])

fhand = open('log-mod.log')
print(fhand)
all_values = []
for line in fhand:
    line = line.rstrip()
    if line.startswith('Channel') : 
        values=line.split()
        chan1 = values[3:-1]
        newvalues = [x[:-1] for x in chan1]
        newvalues = [float(i) for i in newvalues]
        all_values.append(newvalues)
    if not line.startswith('From:') :
        sys.exit('Error in log file- no percentaged flagged by channel')

default_mod = np.mean(all_values[0])+np.mean(all_values[1])/len(all_values[0]+all_values[1])

#now we are going to check the percentage difference between the two, and if it exceeds the required threshold, we are going to check the flagged rows to confirm whether there is a potential transient in the data stream

if default_mod - default_avg >= 1:
    print ('Percentage discrepancy high.  Additional tests...')
    t= pt.table(msname,readonly=True)
    t1 = t.sort('TIME')
    time=t.getcol('TIME')
    tf = t.query('FLAG_ROW = True')
    if len(tf) >= 1:
        print('Flagged rows detected.')
    if not len(tf) >= 1:
        sys.exit('No flagged rows in data set.')
    for t1 in t.iter('TIME', sort=True):
        flagged = t.query('ANTENNA1 != ANTENNA2 && FLAG_ROW = T')
        flagged_num = flagged.nrows()
        not_flagged = t.query('ANTENNA1 != ANTENNA2 && FLAG_ROW = F')
        not_flagged_num = not_flagged.nrows()
        
        if not_flagged <= flagged:
            print ('Potential transient. Check data stream.')

        if not_flagged >= flagged:
            sys.exit('No potential transient detected.')
        
if not default_mod - default_avg >= 1:
    sys.exit('Default and modified flaggers within desired range. No potential transient detected.')
    



