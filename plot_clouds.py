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
variable_name = 'precip_clouds'

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
    print('Using file '+file[0])
    dset = xr.open_dataset(file[0])
    dset = dset.metpy.parse_cf()

    time = pd.to_datetime(dset.time.values)
    increments = (time[1:] - time[:-1]) / pd.Timedelta('1 hour') 
    cum_hour=np.array((time-time[0]) / pd.Timedelta('1 hour')).astype("int")

    # Compute rain and snow 
    rain_acc = dset['RAIN_GSP'] + dset['RAIN_CON']
    snow_acc = dset['SNOW_GSP'] + dset['SNOW_CON']
    rain = rain_acc.diff(dim='time', n=1)
    snow = snow_acc.diff(dim='time', n=1)
    # Unfortunately we have to convert to Numpy array 
    rain = rain.values / increments.values[:, np.newaxis]
    snow = snow.values / increments.values[:, np.newaxis]
    rain = np.insert(arr=rain, obj=0, axis=0, values=np.zeros_like(rain[0]))
    snow = np.insert(arr=snow, obj=0, axis=0, values=np.zeros_like(snow[0]))

    mslp = dset['prmsl'].metpy.unit_array.to('hPa')
    clouds = dset['CLCT']

    lon, lat = get_coordinates(dset)

    levels_rain   = (0.1, 0.2, 0.4, 0.6, 0.8, 1., 1.5, 2., 2.5, 3.0, 4.,
                     5, 7.5, 10., 15., 20., 30., 40., 60., 80., 100., 120.)
    levels_snow   = (0.1, 0.2, 0.4, 0.6, 0.8, 1., 1.5, 2., 2.5, 3.0, 4.,
                     5, 7.5, 10., 15.)
    levels_clouds = np.arange(30, 100, 5)
    levels_mslp   = np.arange(mslp.min().astype("int"), mslp.max().astype("int"), 7.)

    cmap_snow, norm_snow = get_colormap_norm("snow", levels_snow)
    cmap_rain, norm_rain = get_colormap_norm("rain_new", levels_rain)
    cmap_clouds = truncate_colormap(plt.get_cmap('Greys'), 0., 0.5)

    for projection in projections:# This works regardless if projections is either single value or array
        fig = plt.figure(figsize=(figsize_x, figsize_y))
        ax  = plt.gca()
        m, x, y =get_projection(lon, lat, projection)

        m.drawmapboundary(fill_color='whitesmoke')
        m.fillcontinents(color='lightgray',lake_color='whitesmoke', zorder=1)

        # Create a mask to retain only the points inside the globe
        # to avoid a bug in basemap and a problem in matplotlib
        mask = np.logical_or(x<1.e20, y<1.e20)
        x = np.compress(mask,x)
        y = np.compress(mask,y)

        # All the arguments that need to be passed to the plotting function
        args=dict(m=m, x=x, y=y, ax=ax,
                 rain=np.compress(mask, rain, axis=1), snow=np.compress(mask, snow, axis=1),
                 mslp=np.compress(mask, mslp, axis=1), clouds=np.compress(mask, clouds, axis=1),
                 levels_mslp=levels_mslp, levels_rain=levels_rain, levels_snow=levels_snow,
                 levels_clouds=levels_clouds, time=time, projection=projection, cum_hour=cum_hour,
                 cmap_rain=cmap_rain, cmap_snow=cmap_snow, cmap_clouds=cmap_clouds,
                 norm_snow=norm_snow, norm_rain=norm_rain)
        
        print('Pre-processing finished, launching plotting scripts')
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

        cs_rain = args['ax'].tricontourf(args['x'], args['y'], args['rain'][i],
                         extend='max', cmap=args['cmap_rain'], norm=args['norm_rain'],
                         levels=args['levels_rain'], zorder=2)
        cs_snow = args['ax'].tricontourf(args['x'], args['y'], args['snow'][i],
                         extend='max', cmap=args['cmap_snow'], norm=args['norm_snow'],
                         levels=args['levels_snow'], zorder=3)
        cs_clouds = args['ax'].tricontourf(args['x'], args['y'], args['clouds'][i],
                         extend='max', cmap=args['cmap_clouds'],
                         levels=args['levels_clouds'], zorder=1)

        # Unfortunately m.contour with tri = True doesn't work because of a bug 
        c = args['ax'].tricontour(args['x'], args['y'], args['mslp'][i],
                             levels=args['levels_mslp'], colors='red', linewidths=0.5, zorder=4, alpha=0.6)

        labels = args['ax'].clabel(c, c.levels, inline=True, fmt='%4.0f' , fontsize=5)
        an_fc = annotation_forecast(args['ax'],args['time'][i])
        an_var = annotation(args['ax'], 'Clouds, rain, snow and MSLP' ,loc='lower left', fontsize=6)
        an_run = annotation_run(args['ax'], args['time'])

        if first:
            ax_cbar = plt.gcf().add_axes([0.3, 0.1, 0.2, 0.01])
            ax_cbar_2 = plt.gcf().add_axes([0.55, 0.1, 0.2, 0.01])
            cbar_snow = plt.gcf().colorbar(cs_snow, cax=ax_cbar, orientation='horizontal',
             label='Snow [mm/h]')
            cbar_rain = plt.gcf().colorbar(cs_rain, cax=ax_cbar_2, orientation='horizontal',
             label='Rain [mm/h]')
            cbar_snow.ax.tick_params(labelsize=8) 
            cbar_rain.ax.tick_params(labelsize=8)
        
        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **options_savefig)        
        
        remove_collections([c, cs_rain, cs_snow, cs_clouds, labels, an_fc, an_var, an_run])

        first = False 

if __name__ == "__main__":
    main()
