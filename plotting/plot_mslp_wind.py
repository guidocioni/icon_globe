debug = False 
if not debug:
    import matplotlib
    matplotlib.use('Agg')

import matplotlib.pyplot as plt
import xarray as xr 
import metpy.calc as mpcalc
from metpy.units import units
from glob import glob
import numpy as np
import pandas as pd
from multiprocessing import Pool
from functools import partial
import os 
from utils import *
import sys

# The one employed for the figure name when exported 
variable_name = 'winds10m'

print_message('Starting script to plot '+variable_name)

# Get the projection as system argument from the call so that we can 
# span multiple instances of this script outside
if not sys.argv[1:]:
    print_message('Projection not defined, falling back to default (nh, us, world)')
    projections = ['nh','us','world']
else:    
    projections=sys.argv[1:]

def main():
    """In the main function we basically read the files and prepare the variables to be plotted.
    This is not included in utils.py as it can change from case to case."""
    dset, time, cum_hour  = read_dataset(variables=['PMSL', 'VMAX_10M'])


    # Select 850 hPa level using metpy
    winds_10m = dset['VMAX_10M'].load()
    winds_10m.metpy.convert_units('kph')
    mslp = dset['prmsl'].load()
    mslp.metpy.convert_units('hPa')

    lon, lat = get_coordinates()

    levels_winds_10m = np.arange(20., 150., 5.)
    levels_mslp = np.arange(mslp.min().astype("int"), mslp.max().astype("int"), 7.)

    cmap = get_colormap("winds")

    for projection in projections:# This works regardless if projections is either single value or array
        fig = plt.figure(figsize=(figsize_x, figsize_y))
        
        ax  = plt.gca()
        
        m, x, y =get_projection(lon, lat, projection)
        
        m.drawmapboundary(fill_color='whitesmoke')
        m.fillcontinents(color='lightgray',lake_color='whitesmoke', zorder=0)
        # Create a mask to retain only the points inside the globe
        # to avoid a bug in basemap and a problem in matplotlib
        mask = np.logical_or(x<1.e20, y<1.e20)
        x = np.compress(mask,x)
        y = np.compress(mask,y)

        # All the arguments that need to be passed to the plotting function
        args=dict(m=m, x=x, y=y, ax=ax,
                 winds_10m=np.compress(mask, winds_10m, axis=1), mslp=np.compress(mask, mslp, axis=1),
                 levels_winds_10m=levels_winds_10m, levels_mslp=levels_mslp, time=time,
                 projection=projection, cum_hour=cum_hour, cmap=cmap)
        
        print_message('Pre-processing finished, launching plotting scripts')
        if debug:
            plot_files(time[1:2], **args)
        else:
            # Parallelize the plotting by dividing into chunks and processes 
            dates = chunks(time, chunks_size)
            plot_files_param=partial(plot_files, **args)
            p = Pool(processes)
            p.map(plot_files_param, dates)

def plot_files(dates, **args):
    # Using args we don't have to change the prototype function if we want to add other parameters!
    first = True
    for date in dates:
        # Find index in the original array to subset when plotting
        i = np.argmin(np.abs(date - args['time'])) 
        # Build the name of the output image
        if not debug:
            filename = subfolder_images[args['projection']]+'/'+variable_name+'_%s.png' % args['cum_hour'][i]

        cs = args['ax'].tricontourf(args['x'], args['y'], args['winds_10m'][i],
                         extend='max', cmap=args['cmap'], levels=args['levels_winds_10m'])

        # Unfortunately m.contour with tri = True doesn't work because of a bug 
        c = args['ax'].tricontour(args['x'], args['y'], args['mslp'][i],
                             levels=args['levels_mslp'], colors='black', linewidths=0.5)

        labels = args['ax'].clabel(c, c.levels, inline=True, fmt='%4.0f' , fontsize=5)
        an_fc = annotation_forecast(args['ax'],args['time'][i])
        an_var = annotation(args['ax'], 'Accumulated precipitation [mm] and MSLP [hPa]' ,loc='lower left', fontsize=6)
        an_run = annotation_run(args['ax'], args['time'])

        if first:
            plt.colorbar(cs, orientation='horizontal', label='Wind [km/h]', pad=0.03, fraction=0.03)
        
        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **options_savefig)        
        
        remove_collections([c, cs, labels, an_fc, an_var, an_run])

        first = False 

if __name__ == "__main__":
    import time
    start_time=time.time()
    main()
    elapsed_time=time.time()-start_time
    print_message("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))