import matplotlib.pyplot as plt
import numpy as np
from multiprocessing import Pool
from functools import partial
import utils
import sys
from computations import compute_rate

debug = False
if not debug:
    import matplotlib
    matplotlib.use('Agg')


# The one employed for the figure name when exported
variable_name = 'precip_clouds'

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
    dset = utils.read_dataset(variables=['RAIN_GSP', 'RAIN_CON',
                                         'SNOW_GSP', 'SNOW_CON',
                                         'PMSL', 'CLCT'], projection=projection, remapped=True)

    levels_rain = (0.1, 0.2, 0.4, 0.6, 0.8, 1., 1.5, 2., 2.5, 3.0, 4.,
                   5, 7.5, 10., 15., 20., 30., 40., 60., 80., 100., 120.)
    levels_snow = (0.1, 0.2, 0.4, 0.6, 0.8, 1., 1.5, 2., 2.5, 3.0, 4.,
                   5, 7.5, 10., 15.)
    levels_clouds = np.arange(30, 100, 5)

    cmap_snow, norm_snow = utils.get_colormap_norm("snow", levels_snow)
    cmap_rain, norm_rain = utils.get_colormap_norm("rain_new", levels_rain)
    cmap_clouds = utils.truncate_colormap(plt.get_cmap('Greys'), 0.2, 0.7)

    _ = plt.figure(figsize=(utils.figsize_x, utils.figsize_y))
    ax = plt.gca()
    m, x, y, mask = utils.get_projection(dset, projection, remapped=True)
    # Subset dataset only on the area
    dset = dset.where(mask, drop=True)
    m.drawmapboundary(fill_color='whitesmoke')
    m.fillcontinents(color='lightgray', lake_color='whitesmoke', zorder=1)

    dset = compute_rate(dset)
    dset = dset.drop(['lon', 'lat', 'RAIN_GSP', 'RAIN_CON',
                     'SNOW_GSP', 'SNOW_CON']).load()
    dset['prmsl'] = dset['prmsl'].metpy.convert_units('hPa').metpy.dequantify()
    levels_mslp = np.arange(dset['prmsl'].min().astype("int"),
                            dset['prmsl'].max().astype("int"), 5.)

    # All the arguments that need to be passed to the plotting function
    args = dict(m=m, x=x, y=y, ax=ax,
                levels_mslp=levels_mslp, levels_rain=levels_rain, levels_snow=levels_snow,
                levels_clouds=levels_clouds, time=dset.time,
                cmap_rain=cmap_rain, cmap_snow=cmap_snow, cmap_clouds=cmap_clouds,
                norm_snow=norm_snow, norm_rain=norm_rain)

    utils.print_message('Pre-processing finished, launching plotting scripts')
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

        cs_rain = args['ax'].contourf(args['x'], args['y'], data['rain_rate'],
                                      extend='max', cmap=args['cmap_rain'], norm=args['norm_rain'],
                                      levels=args['levels_rain'], zorder=4, antialiased=True)
        cs_snow = args['ax'].contourf(args['x'], args['y'], data['snow_rate'],
                                      extend='max', cmap=args['cmap_snow'], norm=args['norm_snow'],
                                      levels=args['levels_snow'], zorder=5)
        cs_clouds = args['ax'].contourf(args['x'], args['y'], data['CLCT'],
                                        extend='max', cmap=args['cmap_clouds'],
                                        levels=args['levels_clouds'], zorder=3)

        c = args['ax'].contour(args['x'], args['y'], data['prmsl'],
                               levels=args['levels_mslp'], colors='whitesmoke',
                               linewidths=1, zorder=7, alpha=1.0)

        labels = args['ax'].clabel(
            c, c.levels, inline=True, fmt='%4.0f', fontsize=6)

        maxlabels = utils.plot_maxmin_points(args['ax'], args['x'], args['y'], data['prmsl'],
                                             'max', 200, symbol='H', color='royalblue', random=True)
        minlabels = utils.plot_maxmin_points(args['ax'], args['x'], args['y'], data['prmsl'],
                                             'min', 200, symbol='L', color='coral', random=True)

        an_fc = utils.annotation_forecast(args['ax'], time)
        an_var = utils.annotation(
            args['ax'], 'Clouds, rain, snow and MSLP', loc='lower left', fontsize=6)
        an_run = utils.annotation_run(args['ax'], run)

        if first:
            ax_cbar, ax_cbar_2 = utils.divide_axis_for_cbar(args['ax'])
            cbar_snow = plt.gcf().colorbar(cs_snow, cax=ax_cbar, orientation='horizontal',
                                           label='Snow [mm/h]')
            cbar_rain = plt.gcf().colorbar(cs_rain, cax=ax_cbar_2, orientation='horizontal',
                                           label='Rain [mm/h]')

        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **utils.options_savefig)

        utils.remove_collections(
            [c, cs_rain, cs_snow, cs_clouds, labels, an_fc, an_var, an_run, maxlabels, minlabels])

        first = False


if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    elapsed_time = time.time()-start_time
    utils.print_message(
        "script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
