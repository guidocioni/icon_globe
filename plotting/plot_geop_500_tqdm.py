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
from functools import partial
import os 
from utils import *
import sys
from tqdm.contrib.concurrent import process_map

# The one employed for the figure name when exported 
variable_name = 'gph_500'

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
    dset, time, cum_hour  = read_dataset(variables=['T', 'FI'])

    # Select 850 hPa level using metpy
    temp_850 = dset['t'].metpy.sel(vertical=850 * units.hPa).load()
    temp_850.metpy.convert_units('degC')
    z_500 = dset['z'].metpy.sel(vertical=500 * units.hPa).load()
    gph_500 = mpcalc.geopotential_to_height(z_500)
    gph_500 = xr.DataArray(gph_500, coords=z_500.coords,
                           attrs={'standard_name': 'geopotential height',
                                  'units': gph_500.units})

    del z_500

    lon, lat = get_coordinates()

    levels_temp = np.arange(-35., 30., 1.)
    levels_gph = np.arange(4800., 5800., 70.)

    cmap = get_colormap("temp")
    
    for projection in projections:# This works regardless if projections is either single value or array
        # Do preprocessing 
        

        fig = plt.figure(figsize=(figsize_x, figsize_y))
        ax  = plt.gca()

        _, x, y = get_projection(lon, lat, projection)

        # Create a mask to retain only the points inside the globe
        # to avoid a bug in basemap and a problem in matplotlib
        mask = np.logical_or(x<1.e20, y<1.e20)
        x = np.compress(mask, x)
        y = np.compress(mask, y)

        # All the arguments that need to be passed to the plotting function
        args=dict(x=x, y=y, ax=ax,
                 temp_850=np.compress(mask, temp_850, axis=1), 
                 gph_500=np.compress(mask, gph_500, axis=1),
                 levels_temp=levels_temp, cmap=cmap,
                 levels_gph=levels_gph, time=time, projection=projection, cum_hour=cum_hour)

        print_message('Pre-processing finished, launching plotting scripts')
        if debug:
            plot_files(time[0:1], **args)
        else:
            plot_files_param=partial(plot_files, **args)
            r = process_map(plot_files_param, time, max_workers=4)

def plot_files(dates, **args):
    # Using args we don't have to change the prototype function if we want to add other parameters!
    # Find index in the original array to subset when plotting
    i = np.argmin(np.abs(date - args['time'])) 
    # Build the name of the output image
    if not debug:
        filename = subfolder_images[args['projection']]+'/'+variable_name+'_%s.png' % args['cum_hour'][i]

    cs = args['ax'].tricontourf(args['x'], args['y'], args['temp_850'][i], extend='both', cmap=args['cmap'],
                                levels=args['levels_temp'])

    # Unfortunately m.contour with tri = True doesn't work because of a bug 
    c = args['ax'].tricontour(args['x'], args['y'], args['gph_500'][i], levels=args['levels_gph'],
                         colors='white', linewidths=1.)

    labels = args['ax'].clabel(c, c.levels, inline=True, fmt='%4.0f' , fontsize=5)
    an_fc = annotation_forecast(args['ax'],args['time'][i])
    an_var = annotation(args['ax'], 'Geopotential height @500hPa [m] and temperature @850hPa [C]' ,loc='lower left', fontsize=6)
    an_run = annotation_run(args['ax'], args['time'])

    plt.colorbar(cs, orientation='horizontal', label='Temperature', pad=0.03, fraction=0.02)

    if debug:
        plt.show(block=True)
    else:
        plt.savefig(filename, **options_savefig)        

    plt.clf()


if __name__ == "__main__":
    import time
    start_time=time.time()
    main()
    elapsed_time=time.time()-start_time
    print_message("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))