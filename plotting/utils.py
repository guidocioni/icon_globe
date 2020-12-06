import numpy as np
from matplotlib.offsetbox import AnchoredText
import matplotlib.colors as colors
import pandas as pd
from matplotlib.colors import from_levels_and_colors
import seaborn as sns
import os
import matplotlib.patheffects as path_effects
import matplotlib.cm as mplcm
import sys
from glob import glob
import xarray as xr
from matplotlib.colors import BoundaryNorm
import metpy
import re

import warnings
warnings.filterwarnings(
    action='ignore',
    message='The unit of the quantity is stripped.'
)

if 'MODEL_DATA_FOLDER' in os.environ:
    folder = os.environ['MODEL_DATA_FOLDER']
else:
    folder = '/tmp/icon-globe/'
input_file=folder+'ICON_*.nc' 
folder_images = folder
chunks_size = 10
processes = 9
figsize_x = 14
figsize_y = 9

if "HOME_FOLDER" in os.environ:
    home_folder = os.environ['HOME_FOLDER']
else:
    home_folder = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# Options for savefig
options_savefig={
    'dpi':100,
    'bbox_inches':'tight',
    'transparent':True

}

# Dictionary to map the output folder based on the projection employed
subfolder_images={
    'nh' : folder_images,
    'us' : folder_images+'us',
    'world' : folder_images+'world'    
}

folder_glyph = home_folder + '/plotting/yrno_png/'
WMO_GLYPH_LOOKUP_PNG={
        '0': '01',
        '1': '02',
        '2': '02',
        '3': '04',
        '5': '15',
        '10': '15',
        '14': '15',
        '30': '15',
        '40': '15',
        '41': '15',
        '42': '15',
        '43': '15',
        '44': '15',
        '45': '15',
        '46': '15',
        '47': '15',
        '50': '46',
        '53': '46',
        '55': '46',
        '60': '09',
        '61': '09',
        '63': '10',
        '64': '41',
        '65': '12',
        '68': '47',
        '69': '48',
        '70': '13',
        '71': '49',
        '73': '50',
        '74': '45',
        '75': '48',
        '80': '05',
        '81': '05',
        '83': '41',
        '84': '32',
        '85': '08',
        '86': '34',
        '87': '45',
        '89': '43',
        '90': '30',
        '91': '30',
        '92': '25',
        '93': '33',
        '94': '34',
        '95': '25',
}

proj_defs = {
    'nh':
    {
        'projection': 'nsper',
        'lon_0': -25,
        'lat_0': 50,
        'resolution': 'l',
        'satellite_height': 4e6
    },
    'us':
    {
        'projection': 'nsper',
        'lon_0': -100,
        'lat_0': 45,
        'resolution': 'l',
        'satellite_height': 4e6
    },
    'world':
    {
        'projection': 'kav7',
        'lon_0': 0,
        'resolution': 'c'
    },
    'nh_polar':
    {
        'projection': 'npaeqd',
        'boundinglat': 30,
        'lon_0':0,
        'resolution': 'l'
    }
}

def read_dataset(variables = ['T_2M', 'TD_2M'], level=None,
    engine='scipy'):
    """Wrapper to initialize the dataset"""
    # Create the regex for the files with the needed variables
    variables_search = '('+'|'.join(variables)+')'
    # Get a list of all the files in the folder
    # In the future we can use Run/Date to have a more selective glob pattern
    files = glob(folder+'*.nc')
    run = pd.to_datetime(re.findall(r'(?:\d{10})', files[0])[0],
               format='%Y%m%d%H')
    # find only the files with the variables that we need 
    needed_files = [f for f in files if re.search(r'/%s(?:_\d{10})' % variables_search, f)]
    dset = xr.open_mfdataset(needed_files, preprocess=preprocess, engine=engine)
    # NOTE!! Even though we use open_mfdataset, which creates a Dask array, we then 
    # load the dataset into memory since otherwise the object cannot be pickled by 
    # multiprocessing
    dset = dset.metpy.parse_cf()
    if level:
        dset = dset.sel(plev=level, method='nearest')

    dset['run'] = run

    return dset


def get_time_run_cum(dset):
    time = dset['time'].to_pandas()
    run = dset['run'].to_pandas()
    cum_hour = np.array((time - run) / pd.Timedelta('1 hour')).astype(int)

    return time, run, cum_hour


def preprocess(ds):
    '''Additional preprocessing step to apply to the datasets'''
    # correct gust attributes typo
    if 'VMAX_10M' in ds.variables.keys():
        ds['VMAX_10M'].attrs['units'] = 'm/s'
    if 'plev_bnds' in ds.variables.keys():
        ds = ds.drop('plev_bnds')

    return ds.squeeze(drop=True)

def print_message(message):
    """Formatted print"""
    print(os.path.basename(sys.argv[0])+' : '+message)


def get_weather_icons(ww, time):
    #from matplotlib._png import read_png
    from matplotlib.image import imread as read_png
    """
    Get the path to a png given the weather representation 
    """
    weather = []
    for w in ww.values:
        if w.astype(int).astype(str) in WMO_GLYPH_LOOKUP_PNG:
            weather.append(WMO_GLYPH_LOOKUP_PNG[w.astype(int).astype(str)])
        else:
            weather.append('empty')
    weather_icons=[]
    for date, weath in zip(time, weather):
        if date.hour >= 6 and date.hour <= 18:
            add_string='d'
        elif date.hour >=0 and date.hour < 6:
            add_string='n'
        elif date.hour >18 and date.hour < 24:
            add_string='n'

        pngfile=folder_glyph+'%s.png' % (weath+add_string)
        if os.path.isfile(pngfile):
            weather_icons.append(read_png(pngfile))
        else:
            pngfile=folder_glyph+'%s.png' % weath
            weather_icons.append(read_png(pngfile))

    return(weather_icons)


def get_coordinates():
    """Get the lat/lon coordinates from the dataset and convert them to degrees.
    I'm converting them again to an array since metpy does some weird things on 
    the array."""
    files = glob(folder+'invariant_*_global.nc')
    dset = xr.open_dataset(files[0]).squeeze()

    longitude = dset['tlon'].values
    latitude = dset['tlat'].values

    return(longitude, latitude)


def get_city_coordinates(city):
    """Get the lat/lon coordinates of a city given its name using geopy."""
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent='meteogram')
    loc = geolocator.geocode(city)
    return(loc.longitude, loc.latitude)


def get_projection(dset, projection="nh", countries=True, regions=False, labels=False):
    from mpl_toolkits.basemap import Basemap
    """Create the projection in Basemap and returns the x, y array to use it in a plot"""
    lon, lat = get_coordinates()
    proj_options =proj_defs[projection]
    m = Basemap(**proj_options)
    if projection=="us":
        m.drawstates(linewidth=0.5, linestyle='solid', color='black', zorder=5)

    m.drawcoastlines(linewidth=0.5, linestyle='solid', color='black', zorder=5)
    if countries:
        m.drawcountries(linewidth=0.5, linestyle='solid', color='black', zorder=5)
    if projection=="world":
        m.drawcountries(linewidth=0.5, linestyle='solid', color='white', zorder=5)
    if labels:
        m.drawparallels(np.arange(-90.0, 90.0, 10.), linewidth=0.2, color='white',
            labels=[True, False, False, True], fontsize=7)
        m.drawmeridians(np.arange(0.0, 360.0, 10.), linewidth=0.2, color='white',
            labels=[True, False, False, True], fontsize=7)

    x, y = m(lon, lat)

    # Create a mask to retain only the points inside the globe
    # to avoid a bug in basemap and a problem in matplotlib
    mask = np.logical_or(x < 1.e20, y < 1.e20)
    x = np.compress(mask, x)
    y = np.compress(mask, y)

    return m, x, y, mask

# def get_projection_cartopy(plt, lon, lat, projection="nh"):
#     """Create the projection in cartopy and returns the x, y array to use it in a plot"""
#     import cartopy.crs as ccrs
#     import cartopy.feature as cfeature

#     if projection=="nh":
#         proj = ccrs.NearsidePerspective(
#                             central_latitude=50.,
#                             central_longitude=-25.,
#                             satellite_height=4e6)
#     elif projection=="us":
#         proj = ccrs.NearsidePerspective(
#                             central_latitude=45.,
#                             central_longitude=-100.,
#                             satellite_height=4e6)
#     elif projection=="world":
#         proj = ccrs.Mollweide()

#     ax = plt.axes(projection=proj)

#     if projection!="world":
#         ax.coastlines(resolution='50m')
#         ax.add_feature(cfeature.BORDERS.with_scale('50m'), zorder=5)
#     else:
#         ax.coastlines(resolution='110m')
#         ax.add_feature(cfeature.BORDERS.with_scale('110m'), zorder=5)

#     if projection=="us":
#         states_provinces = cfeature.NaturalEarthFeature(
#         category='cultural',
#         name='admin_1_states_provinces_lines',
#         scale='50m',
#         facecolor='none')
#         ax.add_feature(states_provinces, edgecolor='gray')
    
#     x, y, _ = proj.transform_points(ccrs.PlateCarree(), lon, lat).T
    
#     return(ax, x, y)

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def chunks_dataset(ds, n):
    """Same as 'chunks' but for the time dimension in
    a dataset"""
    for i in range(0, len(ds.time), n):
        yield ds.isel(time=slice(i, i + n))


# Annotation run, models 
def annotation_run(ax, time, loc='upper right',fontsize=8):
    """Put annotation of the run obtaining it from the
    time array passed to the function."""
    time = pd.to_datetime(time)
    at = AnchoredText('Run %s'% time.strftime('%Y%m%d %H UTC'), 
                       prop=dict(size=fontsize), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    at.zorder = 10
    ax.add_artist(at)
    return(at)

def annotation(ax, text, loc='upper right',fontsize=8):
    """Put a general annotation in the plot."""
    at = AnchoredText('%s'% text, prop=dict(size=fontsize), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    ax.add_artist(at)
    return(at)

def annotation_forecast(ax, time, loc='upper left', fontsize=8, local=False):
    """Put annotation of the forecast time."""
    time = pd.to_datetime(time)
    if local: # convert to local time
        time = convert_timezone(time)
        at = AnchoredText('Valid %s' % time.strftime('%A %d %b %Y at %H (Berlin)'), 
                       prop=dict(size=fontsize), frameon=True, loc=loc)
    else:
        at = AnchoredText('Forecast for %s' % time.strftime('%A %d %b %Y at %H UTC'), 
                       prop=dict(size=fontsize), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    at.zorder = 10
    ax.add_artist(at)
    return(at)


def add_logo_on_map(ax, logo=home_folder+'/plotting/meteoindiretta_logo.png', zoom=0.15, pos=(0.92, 0.1)):
    '''Add a logo on the map given a pnd image, a zoom and a position
    relative to the axis ax.'''
    img_logo = OffsetImage(read_png(logo), zoom=zoom)
    logo_ann = AnnotationBbox(
        img_logo, pos, xycoords='axes fraction', frameon=False)
    logo_ann.set_zorder(10)
    at = ax.add_artist(logo_ann)
    return at


def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=256):
    """Truncate a colormap by specifying the start and endpoint."""
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return(new_cmap)


def get_colormap(cmap_type):
    """Create a custom colormap."""
    colors_tuple = pd.read_csv(home_folder + '/plotting/cmap_%s.rgba' % cmap_type).values 
    
    cmap = colors.LinearSegmentedColormap.from_list(cmap_type, colors_tuple, colors_tuple.shape[0])
    return(cmap)


def get_colormap_norm(cmap_type, levels):
    """Create a custom colormap."""
    if cmap_type == "rain":
        cmap, norm = from_levels_and_colors(levels, sns.color_palette("Blues", n_colors=len(levels)),
                                                    extend='max')
    elif cmap_type == "snow":
        cmap, norm = from_levels_and_colors(levels, sns.color_palette("PuRd", n_colors=len(levels)),
                                                    extend='max')
    elif cmap_type == "snow_discrete":    
        colors = ["#DBF069","#5AE463","#E3BE45","#65F8CA","#32B8EB",
                    "#1D64DE","#E97BE4","#F4F476","#E78340","#D73782","#702072"]
        cmap, norm = from_levels_and_colors(levels, colors, extend='max')
    elif cmap_type == "rain_acc":    
        cmap, norm = from_levels_and_colors(levels, sns.color_palette('gist_stern_r', n_colors=len(levels)),
                         extend='max')
    elif cmap_type == "rain_new":
        colors_tuple = pd.read_csv(home_folder + '/plotting/cmap_prec.rgba').values    
        cmap, norm = from_levels_and_colors(levels, sns.color_palette(colors_tuple, n_colors=len(levels)),
                         extend='max')
    elif cmap_type == "winds":
        colors_tuple = pd.read_csv(home_folder + '/plotting/cmap_winds.rgba').values    
        cmap, norm = from_levels_and_colors(levels, sns.color_palette(colors_tuple, n_colors=len(levels)),
                         extend='max')

    return(cmap, norm)
def remove_collections(elements):
    """Remove the collections of an artist to clear the plot without
    touching the background, which can then be used afterwards."""
    for element in elements:
        try:
            for coll in element.collections: 
                coll.remove()
        except AttributeError:
            try:
                for coll in element:
                    coll.remove()
            except ValueError:
                print('WARNING: Collection is empty')
            except TypeError:
                element.remove() 
        except ValueError:
            print('WARNING: Collection is empty')


def plot_maxmin_points(ax, lon, lat, data, extrema, nsize, symbol, color='k',
                       random=False):
    """
    This function will find and plot relative maximum and minimum for a 2D grid. The function
    can be used to plot an H for maximum values (e.g., High pressure) and an L for minimum
    values (e.g., low pressue). It is best to used filetered data to obtain  a synoptic scale
    max/min value. The symbol text can be set to a string value and optionally the color of the
    symbol and any plotted value can be set with the parameter color
    lon = plotting longitude values (2D)
    lat = plotting latitude values (2D)
    data = 2D data that you wish to plot the max/min symbol placement
    extrema = Either a value of max for Maximum Values or min for Minimum Values
    nsize = Size of the grid box to filter the max and min values to plot a reasonable number
    symbol = String to be placed at location of max/min value
    color = String matplotlib colorname to plot the symbol (and numerica value, if plotted)
    plot_value = Boolean (True/False) of whether to plot the numeric value of max/min point
    The max/min symbol will be plotted on the current axes within the bounding frame
    (e.g., clip_on=True)
    """
    from scipy.ndimage.filters import maximum_filter, minimum_filter

    # We have to first add some random noise to the field, otherwise it will find many maxima
    # close to each other. This is not the best solution, though...
    if random:
        data = np.random.normal(data, 0.2)

    if (extrema == 'max'):
        data_ext = maximum_filter(data, nsize, mode='nearest')
    elif (extrema == 'min'):
        data_ext = minimum_filter(data, nsize, mode='nearest')
    else:
        raise ValueError('Value for hilo must be either max or min')

    mxy, mxx = np.where(data_ext == data)
    # Filter out points on the border 
    mxx, mxy = mxx[(mxy != 0) & (mxx != 0)], mxy[(mxy != 0) & (mxx != 0)]

    texts = []
    for i in range(len(mxy)):
        texts.append( ax.text(lon[mxy[i], mxx[i]], lat[mxy[i], mxx[i]], symbol, color=color, size=15,
                clip_on=True, horizontalalignment='center', verticalalignment='center',
                path_effects=[path_effects.withStroke(linewidth=1, foreground="black")], zorder=6) )
        texts.append( ax.text(lon[mxy[i], mxx[i]], lat[mxy[i], mxx[i]], '\n' + str(data[mxy[i], mxx[i]].astype('int')),
                color="gray", size=10, clip_on=True, fontweight='bold',
                horizontalalignment='center', verticalalignment='top', zorder=6) )
    return(texts)

