import numpy as np
from multiprocessing import Pool
from functools import partial
from utils import *
import sys
from computations import compute_spacing, compute_theta, compute_pv

debug = False
if not debug:
    import matplotlib
    matplotlib.use('Agg')

import matplotlib.pyplot as plt

# The one employed for the figure name when exported 
variable_name = 'pv_250'

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
    dset = read_dataset(variables=['U', 'V', 'T', 'PMSL'],
                        level=[15000, 25000, 30000],
                        projection=projection, remapped=True)

    if projection != 'world':
        levels_pv = np.linspace(-0.5e-5, 1.6e-5, 30)
    else:
        levels_pv = np.linspace(-1.5e-5, 1.6e-5, 50)

    cmap = get_colormap('temp')

    _ = plt.figure(figsize=(figsize_x, figsize_y))
    ax = plt.gca()
    m, x, y, mask = get_projection(dset, projection, remapped=True)
    m.fillcontinents(color='lightgray', lake_color='whitesmoke', zorder=0)
    # Subset dataset only on the area
    dset = dset.where(mask, drop=True)
    dset = compute_spacing(dset)
    dset = compute_theta(dset)

    dset = dset.load()

    dset['prmsl'].metpy.convert_units('hPa')
    levels_mslp = np.arange(dset['prmsl'].min().astype("int"),
        dset['prmsl'].max().astype("int"), 5.)

    # All the arguments that need to be passed to the plotting function
    args = dict(x=x, y=y, ax=ax,
             levels_pv=levels_pv,
             levels_mslp=levels_mslp,
             cmap=cmap)

    print_message(sys.argv[0]+': Pre-processing finished, launching plotting scripts')
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
        data = compute_pv(data)
        time, run, cum_hour = get_time_run_cum(data)
        # Build the name of the output image
        filename = subfolder_images[projection] + '/' + variable_name + '_%s.png' % cum_hour

        cs = args['ax'].contourf(args['x'], args['y'],
                                    data['pv'].sel(plev=25000),
                                    extend='max', cmap=args['cmap'],
                                    levels=args['levels_pv'])

        c = args['ax'].contour(args['x'], args['y'], data['prmsl'],
                             levels=args['levels_mslp'], colors='white', linewidths=1)


        labels = args['ax'].clabel(c, c.levels, inline=True, fmt='%4.0f' , fontsize=5)

        maxlabels = plot_maxmin_points(args['ax'], args['x'], args['y'], data['prmsl'],
                                        'max', 180, symbol='H', color='royalblue', random=True)
        minlabels = plot_maxmin_points(args['ax'], args['x'], args['y'], data['prmsl'],
                                        'min', 180, symbol='L', color='coral', random=True)

        an_fc = annotation_forecast(args['ax'], time)
        an_var = annotation(args['ax'], 'PV @ 250 hPa and MSLP (hPa)',
            loc='lower left', fontsize=6)
        an_run = annotation_run(args['ax'], run)

        if first:
            plt.colorbar(cs, orientation='horizontal', label='PV [%s]' % data['pv'].units, pad=0.03, fraction=0.035)

        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **options_savefig)        

        remove_collections([cs, c, labels, maxlabels, minlabels, an_fc, an_var, an_run])

        first = False


if __name__ == "__main__":
    import time
    start_time=time.time()
    main()
    elapsed_time=time.time()-start_time
    print_message("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
