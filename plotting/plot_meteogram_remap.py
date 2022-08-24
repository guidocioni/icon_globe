import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import xarray as xr 
from metpy.units import units
from glob import glob
import numpy as np
import pandas as pd
import os 
from utils import *
import sys
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
from matplotlib import gridspec
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from tqdm.contrib.concurrent import process_map
import time

print('Starting script to plot meteograms')

# Get the projection as system argument from the call so that we can 
# span multiple instances of this script outside
if not sys.argv[1:]:
    print('City not defined, falling back to default (Hamburg)')
    cities = ['Hamburg']
else:    
    cities=sys.argv[1:]

def main():
    dset = read_dataset(variables=['T_2M','TD_2M','T','VMAX_10M',
                                    'PMSL','WW','RAIN_GSP','RAIN_CON',
                                    'SNOW_GSP','SNOW_CON','RELHUM','U','V'],
                                    engine='scipy',
                                    remapped=True)

    hsurf = xr.open_dataset(glob(folder+'remap/invariant_*_global.nc')[0]).squeeze()['HSURF']
    attrs = dset.attrs
    dset = xr.merge([dset, hsurf])
    dset.attrs = attrs

    it = []
    for city in cities:
        lon, lat = get_city_coordinates(city)
        d = dset.sel(lon=lon, lat=lat, method='nearest').copy().load()
        d.attrs['city'] = city
        it.append(d)
        del d

    process_map(plot, it, max_workers=processes, chunksize=2)

def plot(dset_city):
    city = dset_city.attrs['city']
    print_message('Producing meteogram for %s' % city)
    time, run, cum_hour = get_time_run_cum(dset_city)
    t = dset_city['t']
    t =     t.metpy.convert_units('degC').metpy.dequantify()
    rh = dset_city['r']
    t2m = dset_city['2t']
    t2m =     t2m.metpy.convert_units('degC').metpy.dequantify()
    td2m = dset_city['2d']
    td2m =     td2m.metpy.convert_units('degC').metpy.dequantify()
    vmax_10m = dset_city['VMAX_10M']
    vmax_10m =     vmax_10m.metpy.convert_units('kph').metpy.dequantify()
    pmsl = dset_city['prmsl']
    pmsl =     pmsl.metpy.convert_units('hPa').metpy.dequantify()
    plevs = dset_city['t'].metpy.vertical.metpy.unit_array.to('hPa').magnitude

    rain_acc = dset_city['RAIN_GSP'] + dset_city['RAIN_CON']
    snow_acc = dset_city['SNOW_GSP'] + dset_city['SNOW_CON']
    rain = rain_acc.differentiate(coord="time", datetime_unit="h")
    snow = snow_acc.differentiate(coord="time", datetime_unit="h")

    weather_icons = get_weather_icons(dset_city['WW'], time)

    fig = plt.figure(figsize=(10, 12))
    gs = gridspec.GridSpec(4, 1, height_ratios=[3, 1, 1, 1])

    ax0 = plt.subplot(gs[0])
    cs = ax0.contourf(time, plevs, t.T, extend='both',
                      cmap=get_colormap("temp"), levels=np.arange(-70, 35, 5))
    ax0.axes.get_xaxis().set_ticklabels([])
    ax0.invert_yaxis()
    ax0.set_ylim(1000, 200)
    ax0.set_xlim(time[0], time[-1])
    ax0.set_ylabel('Pressure [hPa]')
    y_labels = ax0.get_yticks()
    cbar_ax = fig.add_axes([0.92, 0.55, 0.02, 0.3])
    cmap_new = truncate_colormap(plt.get_cmap('gray_r'), 0.1, 0.6)
    cs2 = ax0.contour(time, plevs, rh.T,
                      levels=[25, 50, 100], cmap=cmap_new, alpha=0.7)
    labels = ax0.clabel(cs2, cs2.levels, inline=True, fmt='%4.0f' , fontsize=6)

    dset_winds = dset_city.sel(time=pd.date_range(
                               time[0], time[-1], freq='6H'))
    v = ax0.barbs(pd.to_datetime(dset_winds.time.values),
                  plevs, dset_winds['u'].T, dset_winds['v'].T,
                  alpha=0.3, length=5.5)
    ax0.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    ax0.grid(True, alpha=0.5)
    an_fc = annotation_run(ax0, run)
    an_var = annotation(ax0, 'RH, $T$ and winds @(%3.1fN, %3.1fE, %d m)' % (dset_city.lat, dset_city.lon, dset_city.HSURF),
                        loc='upper left')
    an_city = annotation(ax0, city, loc='upper center')

    ax1 = plt.subplot(gs[1])
    ax1.set_xlim(time[0], time[-1])
    ts = ax1.plot(time, t2m, label='2m $T$', color='darkcyan')
    ts1 = ax1.plot(
        time, td2m, label='2m $T_d$', color='darkcyan', linestyle='dashed')
    ax1.axes.get_xaxis().set_ticklabels([])
    plt.legend(fontsize=7)
    ax1.set_ylabel('2m $T$, $T_d$ [$^{\circ}$C]')
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    ax1.grid(True, alpha=0.5)

    for dt, weather_icon, dewp in zip(time, weather_icons, t2m):
        imagebox = OffsetImage(weather_icon, zoom=.025)
        ab = AnnotationBbox(
            imagebox, (mdates.date2num(dt), dewp), frameon=False)
        ax1.add_artist(ab)

    ax2 = plt.subplot(gs[2])
    ax2.set_xlim(time[0], time[-1])
    ts = ax2.plot(time, vmax_10m,
                  label='Gusts', color='lightcoral')
    ax2.set_ylabel('Wind gust [km/h]')
    ax22 = ax2.twinx()
    ts1 = ax22.plot(time, pmsl, label='MSLP', color='m')
    ax2.axes.get_xaxis().set_ticklabels([])
    ax22.set_ylabel('MSLP [hPa]')
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    ax2.grid(True, alpha=0.5)

    # Collect all the elements for the legend
    handles, labels = [], []
    for ax in (ax2, ax22):
        for h, l in zip(*ax.get_legend_handles_labels()):
            handles.append(h)
            labels.append(l)
    plt.legend(handles, labels, fontsize=7)

    ax3 = plt.subplot(gs[3])
    ax3.set_xlim(time[0], time[-1])
    ts = ax3.plot(time, rain_acc, label='Rain (acc.)',
                  color='dodgerblue', linewidth=0.1)
    ts1 = ax3.plot(time, snow_acc, label='Snow (acc.)',
                   color='orchid', linewidth=0.1)
    ax3.fill_between(time, rain_acc, y2=0, facecolor='dodgerblue', alpha=0.2)
    ax3.fill_between(time, snow_acc, y2=0, facecolor='orchid', alpha=0.2)
    ax3.set_ylim(bottom=0)
    ax3.set_ylabel('Accum. [mm]')
    ax33 = ax3.twinx()
    ts2 = ax33.plot(time, rain, label='Rain', color='dodgerblue')
    ts3 = ax33.plot(time, snow, label='Snow', color='orchid')
    ax33.set_ylim(bottom=0)
    ax33.set_ylabel('Inst. [mm h$^{-1}$]')
    ax33.legend(fontsize=7)

    ax3.grid(True, alpha=0.5)
    ax3.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    ax3.xaxis.set_major_formatter(DateFormatter('%d %b %HZ'))
    for tick in ax3.get_xticklabels():
        tick.set_rotation(45)
        tick.set_horizontalalignment('right')

    fig.subplots_adjust(hspace=0.1)
    fig.colorbar(cs, orientation='vertical',
                 label='Temperature [C]', cax=cbar_ax)

    # Build the name of the output image
    filename = folder_images + '/meteogram_%s.png' % city
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.clf()

if __name__ == "__main__":
    import time
    start_time=time.time()
    main()
    elapsed_time=time.time()-start_time
    print_message("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))