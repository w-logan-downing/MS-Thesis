from datetime import datetime, timedelta
import pygrib
import numpy as np
import pandas as pd
import xarray as xr

import sys
# Note: To use this script, you'll need to set up the conda environment and download the code
# developed by Brian Blaylock. See https://github.com/blaylockbk/pyBKB_v3.
sys.path.append('/home/wdownin/pyBKB_v3')
from BB_HRRR.HRRR_Pando import *

# Note: You're getting grid relative u and v wind components, this will need to be converted later more than likely.
#variables = ['VIS:surface', 'GUST:surface'] # for debugging
#variables = ['VIS:surface', 'GUST:surface', 'TMP:surface', 'CNWAT:surface', 'WEASD:surface', 'SNOWC:surface',
#       'SNOD:surface', 'TMP:2 m', 'POT:2 m', 'SPFH:2 m', 'DPT:2 m', 'RH:2 m', 'UGRD:10 m', 'VGRD:10 m',
#       'WIND:10 m', 'MAXUW:10 m', 'MAXVW:10 m', 'CPOFP:surface', 'PRATE:surface', 'APCP:surface',
#       'WEASD:surface', 'FROZR:surface', 'FRZR:surface', 'SSRUN:surface', 'CSNOW:surface', 'CICEP:surface'
#       'CRAIN:surface', 'SFCR:surface', 'FRICV:surface', 'GFLUX:surface', 'CAPE:surface', 'CIN:surface',
#       'DSWRF:surface']

# Revised set removing the vars that caused donwload problems.
variables = ['VIS:surface', 'GUST:surface', 'TMP:surface', 'CNWAT:surface', 'WEASD:surface', 'SNOWC:surface',
       'SNOD:surface', 'TMP:2 m', 'POT:2 m', 'SPFH:2 m', 'DPT:2 m', 'RH:2 m', 'UGRD:10 m', 'VGRD:10 m',
       'WIND:10 m', 'CPOFP:surface', 'PRATE:surface', 'APCP:surface',
       'WEASD:surface', 'FROZR:surface', 'FRZR:surface', 'SSRUN:surface', 'CSNOW:surface', 'CICEP:surface',
       'CRAIN:surface', 'SFCR:surface', 'FRICV:surface', 'GFLUX:surface', 'CAPE:surface', 'CIN:surface',
       'DSWRF:surface']

# Sometimes there will be variables that are missing, to fix this, I'm grabbing a grid from a variable
# that is known to exist on Pando and an empty set is being initialized.
tmp = get_hrrr_variable(datetime(2019,6,1,0,0), 'TMP:2 m')
tmp = hrrr_subset(tmp, half_box=85, lat=39.7684, lon=-86.1581, thin=1, verbose=False)

# Prep an empty set of information to fill the space time cube with in cases where data is missing.
latlon_grid = {'lat': tmp['lat'], 'lon': tmp['lon']}
empty_set = np.full((170,170), np.nan)


sdate = datetime(2017,4,2,0,0)
edate = datetime(2019,4,16,0,0)

dates = pd.date_range(start=sdate, end=edate, freq='H')

# !!!!! Feature to add - It may be worthwile to pull some of the attributes during get_variable 
# step and insert them into the data arrays. 

datasets = []
timeSliceArrays = []

# get variables for each date
for date in dates:
       print('Accessing the following date . . . ')
       print(date)
       ds = xr.Dataset() # Keeps the datasets small to avoid growing datasets too large in a loop.
       for var in variables:
              try:
                     data = get_hrrr_variable(date, var, fxx=0, model='hrrr',
                                          field='sfc', removeFile=True,
                                          value_only=False, verbose=True,
                                          outDIR='/tmp/') #/tmp/ is a cluster directory
                     
                     # lat/lon values have been chosen to center on Indiana
                     data = hrrr_subset(data, half_box=85, lat=39.7684, 
                                   lon=-86.1581, verbose=True)

                     ds[var] = xr.DataArray(data['value'], dims=['y','x'],
                                                        coords = {'lon': (('y','x'), data['lon']),
                                                               'lat': (('y','x'), data['lat']),
                                                               'time': ((), date)}, name = var)
              except:
                     print("The variable you requested is either missing or something else went wrong.")
                     print("I'll fill the time slice with an empty set for you!")
                     ds[var] = xr.DataArray(empty_set, dims=['y','x'],
                                                 coords = {'lon': (('y','x'), latlon_grid['lon']),
                                                        'lat': (('y','x'), latlon_grid['lat']),
                                                        'time': ((), date)}, name = var)

       datasets.append(ds)

# Combine all datasets into a single dataset
# !!!!! You may need to do this in chunks as you write to a file if the data is beg enough.
# This can be done with dask
ds = xr.concat(datasets,dim='time')  

ds.to_netcdf(path='/depot/wwtung/data/LoganD/wxData/hrrr_lowerLevs.nc', mode='w')
