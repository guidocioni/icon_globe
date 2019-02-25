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
variable_name = 'winds_jet'

print('Starting script to plot '+variable_name)

# Get the projection as system argument from the call so that we can 
# span multiple instances of this script outside
if not sys.argv[1:]:
    print('Projection not defined, falling back to default (nh, us, world)')
    projections = ['nh','us','world']
else:    
    projections=sys.argv[1:]

def main():
    """In the main function we basically read the files and prepare the variables to be plotted.
    This is not included in utils.py as it can change from case to case."""
    file = glob(input_file)
    print(sys.argv[0]+': Using file '+file[0])
    dset = xr.open_dataset(file[0])
    dset = dset.metpy.parse_cf()

    # Select 850 hPa level using metpy
    wind_300 = mpcalc.wind_speed(dset['u'].metpy.sel(vertical=300 * units.hPa),
                             dset['v'].metpy.sel(vertical=300 * units.hPa)).to(units.kph)
    gph_300 = mpcalc.geopotential_to_height(dset['z'].metpy.sel(vertical=300 * units.hPa))

    lon, lat = get_coordinates(dset)

    time = pd.to_datetime(dset.time.values)
    cum_hour=np.array((time-time[0]) / pd.Timedelta('1 hour')).astype("int")

    levels_wind = np.arange(50., 300., 10.)
    levels_gph = np.arange(8200., 9700., 100.)

    cmap = truncate_colormap(plt.get_cmap('CMRmap_r'), 0., 0.9)

    for projection in projections:# This works regardless if projections is either single value or array
        fig = plt.figure(figsize=(figsize_x, figsize_y))
        ax  = plt.gca()
        m, x, y =get_projection(lon, lat, projection)
        m.shadedrelief(scale=0.4, alpha=0.8)
        # Create a mask to retain only the points inside the globe
        # to avoid a bug in basemap and a problem in matplotlib
        mask = np.logical_or(x<1.e20, y<1.e20)
        x = np.compress(mask,x)
        y = np.compress(mask,y)

        # All the arguments that need to be passed to the plotting function
        args=dict(m=m, x=x, y=y, ax=ax,
                 wind_300=wind_300, gph_300=gph_300, mask=mask, levels_wind=levels_wind,
                 levels_gph=levels_gph, time=time, projection=projection, cum_hour=cum_hour,
                 cmap=cmap)
        
        print(sys.argv[0]+': Pre-processing finished, launching plotting scripts')
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
        filename = subfolder_images[args['projection']]+'/'+variable_name+'_%s.png' % args['cum_hour'][i]#date.strftime('%Y%m%d%H')#
        # Test if the image already exists, although this behaviour should be removed in the future
        # since we always want to overwrite old files.
        # if os.path.isfile(filename):
        #     print('Skipping '+str(filename))
        #     continue 

        cs = args['ax'].tricontourf(args['x'], args['y'], args['wind_300'][i, args['mask']],
                         extend='max', cmap=args['cmap'],
                         levels=args['levels_wind'])

        # Unfortunately m.contour with tri = True doesn't work because of a bug 
        c = args['ax'].tricontour(args['x'], args['y'], args['gph_300'][i,args['mask']],
                             levels=args['levels_gph'], colors='black', linewidths=0.5)

        labels = args['ax'].clabel(c, c.levels, inline=True, fmt='%4.0f' , fontsize=5)
        annotation(args['ax'],'Forecast for %s' % date.strftime('%d %b %Y at %H UTC') ,loc='upper left')
        annotation(args['ax'], 'Winds [kph] and geopotential [m] @300hPa' ,loc='lower left', fontsize=6)
        annotation_run(args['ax'], args['time'])

        if first:
            plt.colorbar(cs, orientation='horizontal', label='Wind', pad=0.03, fraction=0.02)
        
        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **options_savefig)        
        
        remove_collections([c, cs, labels])

        first = False 

if __name__ == "__main__":
    main()
