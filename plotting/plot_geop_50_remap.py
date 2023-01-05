import numpy as np
from multiprocessing import Pool
from functools import partial
import utils
import sys
from computations import compute_geopot_height
from matplotlib import patheffects

debug = False
if not debug:
    import matplotlib
    matplotlib.use('Agg')

import matplotlib.pyplot as plt

# The one employed for the figure name when exported 
variable_name = 'gpt_50'

utils.print_message('Starting script to plot '+variable_name)

# Get the projection as system argument from the call so that we can 
# span multiple instances of this script outside
if not sys.argv[1:]:
    utils.print_message(
        'Projection not defined, falling back to default (nh)')
    projection = 'nh'
else:
    projection = sys.argv[1]

def main():
    """In the main function we basically read the files and prepare the variables to be plotted.
    This is not included in utils.py as it can change from case to case."""
    dset = utils.read_dataset(variables=['T', 'FI'], level=[5000],
                        projection=projection, remapped=True)

    levels_temp = np.arange(-90, -18, 1)
    levels_gph = np.arange(19500., 21000., 150.)

    cmap = utils.get_colormap('temp_meteociel')

    _ = plt.figure(figsize=(utils.figsize_x, utils.figsize_y))
    ax = plt.gca()
    _, x, y, mask = utils.get_projection(dset, projection, remapped=True)
    # Subset dataset only on the area
    dset = dset.where(mask, drop=True)
    # and then compute what we need
    dset = compute_geopot_height(dset, zvar='z')
    dset = dset.drop(['z', 'lon', 'lat']).squeeze().load()

    # All the arguments that need to be passed to the plotting function
    args=dict(x=x, y=y, ax=ax,
             levels_temp=levels_temp, cmap=cmap,
             levels_gph=levels_gph)

    utils.print_message('Pre-processing finished, launching plotting scripts')
    if debug:
        plot_files(dset.isel(time=slice(-2, -1)), **args)
    else:
        # Parallelize the plotting by dividing into chunks and processes
        dss = utils.chunks_dataset(dset, utils.chunks_size)
        plot_files_param = partial(plot_files, **args)
        p = Pool(utils.processes)
        p.map(plot_files_param, dss)


def plot_files(dss, **args):
    # Using args we don't have to change the prototype function if we want to add other parameters!
    first = True
    for time_sel in dss.time:
        data = dss.sel(time=time_sel)
        data['t'] =         data['t'].metpy.convert_units('degC').metpy.dequantify()
        time, run, cum_hour = utils.get_time_run_cum(data)
        # Build the name of the output image
        filename = utils.subfolder_images[projection] + '/' + variable_name + '_%s.png' % cum_hour

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
                                 linewidths=0.2)


        c = args['ax'].contour(args['x'], args['y'],
                                  data['geop'], levels=args['levels_gph'],
                                  colors='white', linewidths=1.25)

        labels = args['ax'].clabel(c, c.levels, inline=True, fmt='%4.0f' , fontsize=5)

        labels2 = args['ax'].clabel(
            css, css.levels, inline=True, fmt='%4.0f', fontsize=7)
        plt.setp(labels2, path_effects=[
        patheffects.withStroke(linewidth=0.5, foreground="w")])


        maxlabels = utils.plot_maxmin_points(args['ax'], args['x'], args['y'], data['geop'],
                                        'max', 300, symbol='H', color='royalblue', random=True)
        minlabels = utils.plot_maxmin_points(args['ax'], args['x'], args['y'], data['geop'],
                                        'min', 300, symbol='L', color='coral', random=True)


        an_fc = utils.annotation_forecast(args['ax'], time)
        an_var = utils.annotation(args['ax'], 'Geopotential height and temperature @50hPa [m]',
            loc='lower left', fontsize=6)
        an_run = utils.annotation_run(args['ax'], run)

        if first:
            plt.colorbar(cs, orientation='horizontal', label='Temperature', pad=0.03, fraction=0.03)

        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **utils.options_savefig)        

        utils.remove_collections([c, cs, css, labels, labels2, an_fc, an_var, an_run, maxlabels, minlabels])

        first = False 


if __name__ == "__main__":
    import time
    start_time=time.time()
    main()
    elapsed_time=time.time()-start_time
    utils.print_message("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
