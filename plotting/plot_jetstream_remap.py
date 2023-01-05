import matplotlib.pyplot as plt
import numpy as np
from multiprocessing import Pool
from functools import partial
import utils
import sys
from computations import compute_geopot_height, compute_wind_speed

debug = False
if not debug:
    import matplotlib
    matplotlib.use('Agg')


# The one employed for the figure name when exported
variable_name = 'winds_jet'

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
    dset = utils.read_dataset(variables=['U', 'V', 'FI'], level=30000,
                              projection=projection, remapped=True)

    # Select 850 hPa level using metpy
    levels_wind = np.arange(70., 300., 10.)
    levels_gph = np.arange(8200., 11100., 120.)
    cmap = utils.truncate_colormap(plt.get_cmap('CMRmap_r'), 0., 0.9)

    _ = plt.figure(figsize=(utils.figsize_x, utils.figsize_y))
    ax = plt.gca()
    m, x, y, mask = utils.get_projection(dset, projection, remapped=True)
    m.fillcontinents(color='lightgray', lake_color='whitesmoke', zorder=1)
    # Subset dataset only on the area
    dset = dset.where(mask, drop=True)
    dset = compute_wind_speed(dset)
    dset = compute_geopot_height(dset)

    dset = dset.drop(['z', 'u', 'v']).load()

    # All the arguments that need to be passed to the plotting function
    args = dict(x=x, y=y, ax=ax,
                levels_wind=levels_wind, levels_gph=levels_gph,
                time=dset.time, cmap=cmap)

    utils.print_message(
        sys.argv[0]+': Pre-processing finished, launching plotting scripts')
    if debug:
        plot_files(dset.isel(time=slice(0, 2)), **args)
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
        time, run, cum_hour = utils.get_time_run_cum(data)
        # Build the name of the output image
        filename = utils.subfolder_images[projection] + \
            '/' + variable_name + '_%s.png' % cum_hour

        cs = args['ax'].contourf(args['x'], args['y'],
                                 data['wind_speed'],
                                 extend='max', cmap=args['cmap'],
                                 levels=args['levels_wind'])

        # Unfortunately m.contour with tri = True doesn't work because of a bug
        c = args['ax'].contour(args['x'], args['y'], data['geop'],
                               levels=args['levels_gph'], colors='black', linewidths=0.8)

        minlabels = utils.plot_maxmin_points(args['ax'], args['x'], args['y'], data['geop'],
                                             'min', 200, symbol='L', color='coral', random=True)

        labels = args['ax'].clabel(
            c, c.levels, inline=True, fmt='%4.0f', fontsize=5)
        an_fc = utils.annotation_forecast(args['ax'], time)
        an_var = utils.annotation(args['ax'], 'Winds [kph] and geopotential [m] @300hPa',
                                  loc='lower left', fontsize=6)
        an_run = utils.annotation_run(args['ax'], run)

        if first:
            plt.colorbar(cs, orientation='horizontal',
                         label='Wind', pad=0.03, fraction=0.03)

        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **utils.options_savefig)

        utils.remove_collections([c, cs, labels, an_fc, an_var,
                                  an_run, minlabels])

        first = False


if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    elapsed_time = time.time()-start_time
    utils.print_message("script took " + time.strftime("%H:%M:%S",
                                                       time.gmtime(elapsed_time)))
