import numpy as np
from multiprocessing import Pool
from functools import partial
from utils import *
import sys

debug = False
if not debug:
    import matplotlib
    matplotlib.use('Agg')

import matplotlib.pyplot as plt

# The one employed for the figure name when exported 
variable_name = 'winds10m'

print_message('Starting script to plot '+variable_name)

# Get the projection as system argument from the call so that we can 
# span multiple instances of this script outside
if not sys.argv[1:]:
    print_message(
        'Projection not defined, falling back to default (nh)')
    projection = 'nh'
else:
    projection = sys.argv[1]


def main():
    """In the main function we basically read the files and prepare the variables to be plotted.
    This is not included in utils.py as it can change from case to case."""
    dset = read_dataset(variables=['PMSL', 'VMAX_10M', 'U_10M', 'V_10M'], projection=projection, remapped=True)

    levels_winds_10m = np.arange(20., 150., 5.)
    cmap = get_colormap("winds")

    _ = plt.figure(figsize=(figsize_x, figsize_y))
    ax = plt.gca()
    m, x, y, mask = get_projection(dset, projection, remapped=True)
    # Subset dataset only on the area
    dset = dset.where(mask, drop=True)
    m.drawmapboundary(fill_color='whitesmoke')
    m.fillcontinents(color='lightgray', lake_color='whitesmoke', zorder=1)
    # Create a mask to retain only the points inside the globe
    # to avoid a bug in basemap and a problem in matplotlib
    dset = dset.load()
    dset['prmsl'] = dset['prmsl'].metpy.convert_units('hPa').metpy.dequantify()

    levels_mslp = np.arange(dset['prmsl'].min().astype("int"),
        dset['prmsl'].max().astype("int"), 5.)

    # All the arguments that need to be passed to the plotting function
    args=dict(m=m, x=x, y=y, ax=ax,
             levels_winds_10m=levels_winds_10m, levels_mslp=levels_mslp,
             time=dset.time,
             projection=projection, cmap=cmap)

    print_message('Pre-processing finished, launching plotting scripts')
    if debug:
        plot_files(dset.isel(time=slice(-2, -1)), **args)
    else:
        # Parallelize the plotting by dividing into chunks and processes
        dss = chunks_dataset(dset, chunks_size)
        plot_files_param = partial(plot_files, **args)
        p = Pool(processes)
        p.map(plot_files_param, dss)


def plot_files(dss, **args):
    # Using args we don't have to change the prototype function if we want to add other parameters!
    first = True
    for time_sel in dss.time:
        data = dss.sel(time=time_sel)
        data['VMAX_10M'] = data['VMAX_10M'].metpy.convert_units('kph').metpy.dequantify()
        time, run, cum_hour = get_time_run_cum(data)
        # Build the name of the output image
        filename = subfolder_images[projection] + '/' + variable_name + '_%s.png' % cum_hour

        cs = args['ax'].contourf(args['x'], args['y'], data['VMAX_10M'],
                         extend='max', cmap=args['cmap'], levels=args['levels_winds_10m'])

        c = args['ax'].contour(args['x'], args['y'], data['prmsl'],
                             levels=args['levels_mslp'], colors='red', linewidths=1)

        labels = args['ax'].clabel(c, c.levels, inline=True, fmt='%4.0f' , fontsize=5)

        maxlabels = plot_maxmin_points(args['ax'], args['x'], args['y'], data['prmsl'],
                                        'max', 180, symbol='H', color='royalblue', random=True)
        minlabels = plot_maxmin_points(args['ax'], args['x'], args['y'], data['prmsl'],
                                        'min', 180, symbol='L', color='coral', random=True)

        if projection != 'world':
            density = 15
            scale = 5e2
        else:
            density = 35
            scale = 5e2

        cv = args['ax'].quiver(args['x'][::density, ::density],
                               args['y'][::density, ::density],
                               data['10u'][::density, ::density],
                               data['10v'][::density, ::density],
                               scale=scale,
                               alpha=0.5, color='gray', headwidth=2)

        an_fc = annotation_forecast(args['ax'], time)
        an_var = annotation(args['ax'], 'Accumulated precipitation [mm] and MSLP [hPa]' ,loc='lower left', fontsize=6)
        an_run = annotation_run(args['ax'], run)
        logo = add_logo_on_map(ax=args['ax'],
                                zoom=0.1, pos=(0.95, 0.08))

        if first:
            plt.colorbar(cs, orientation='horizontal', label='Wind [km/h]', pad=0.03, fraction=0.03)

        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **options_savefig)        

        remove_collections([c, cs, labels, an_fc, an_var, an_run, cv, maxlabels, minlabels, logo])

        first = False 


if __name__ == "__main__":
    import time
    start_time=time.time()
    main()
    elapsed_time=time.time()-start_time
    print_message("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
