import numpy as np
from multiprocessing import Pool
from functools import partial
from utils import *
import sys
from computations import compute_geopot_height
from matplotlib import patheffects

debug = False
if not debug:
    import matplotlib
    matplotlib.use('Agg')

import matplotlib.pyplot as plt

# The one employed for the figure name when exported 
variable_name = 'gph_50'

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
    dset = read_dataset(variables=['T', 'FI'], level=[5000],
                        projection=projection, remapped=True)

    levels_temp = np.arange(-86, -18, 1)
    levels_gph = np.arange(1970., 2050., 25.)

    cmap = get_colormap('temp_meteociel')

    _ = plt.figure(figsize=(figsize_x, figsize_y))
    ax = plt.gca()
    _, x, y, mask = get_projection(dset, projection, remapped=True)
    # Subset dataset only on the area
    dset = dset.where(mask, drop=True)
    # and then compute what we need
    dset = compute_geopot_height(dset, zvar='z')
    dset = dset.drop(['z', 'lon', 'lat']).squeeze().load()

    # All the arguments that need to be passed to the plotting function
    args=dict(x=x, y=y, ax=ax,
             levels_temp=levels_temp, cmap=cmap,
             levels_gph=levels_gph)

    print_message('Pre-processing finished, launching plotting scripts')
    if debug:
        plot_files(dset.isel(time=slice(0, 2)), **args)
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
        data['t'].metpy.convert_units('degC')
        time, run, cum_hour = get_time_run_cum(data)
        # Build the name of the output image
        filename = subfolder_images[projection] + '/' + variable_name + '_%s.png' % cum_hour

        cs = args['ax'].contourf(args['x'],
                                    args['y'],
                                    data['t'],
                                    extend='both',
                                    cmap=args['cmap'],
                                    levels=args['levels_temp'])

        css = args['ax'].contour(args['x'], args['y'],
                                 data['t'], colors='gray',
                                 levels=args['levels_temp'][::4],
                                 linestyles='solid',
                                 linewidths=0.3)


        c = args['ax'].contour(args['x'], args['y'],
                                  data['geop'], levels=args['levels_gph'],
                                  colors='white', linewidths=1.)

        labels = args['ax'].clabel(c, c.levels, inline=True, fmt='%4.0f' , fontsize=5)

        labels2 = args['ax'].clabel(
            css, css.levels, inline=True, fmt='%4.0f', fontsize=7)
        plt.setp(labels2, path_effects=[
        patheffects.withStroke(linewidth=0.5, foreground="w")])


        maxlabels = plot_maxmin_points(args['ax'], args['x'], args['y'], data['geop'],
                                        'max', 300, symbol='H', color='royalblue', random=True)
        minlabels = plot_maxmin_points(args['ax'], args['x'], args['y'], data['geop'],
                                        'min', 300, symbol='L', color='coral', random=True)


        an_fc = annotation_forecast(args['ax'], time)
        an_var = annotation(args['ax'], 'Geopotential height and temperature @50hPa [m]',
            loc='lower left', fontsize=6)
        an_run = annotation_run(args['ax'], run)

        if first:
            plt.colorbar(cs, orientation='horizontal', label='Temperature', pad=0.03, fraction=0.02)

        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **options_savefig)        

        remove_collections([c, cs, css, labels, labels2, an_fc, an_var, an_run, maxlabels, minlabels])

        first = False 


if __name__ == "__main__":
    import time
    start_time=time.time()
    main()
    elapsed_time=time.time()-start_time
    print_message("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
