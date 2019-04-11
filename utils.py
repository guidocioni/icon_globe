from mpl_toolkits.basemap import Basemap  # import Basemap matplotlib toolkit
import numpy as np
from matplotlib.offsetbox import AnchoredText
import matplotlib.colors as colors
import metpy.calc as mpcalc
from metpy.units import units
import pandas as pd
from matplotlib.colors import from_levels_and_colors
import seaborn as sns
import os
import __main__ as main

import warnings
warnings.filterwarnings(
    action='ignore',
    message='The unit of the quantity is stripped.'
)

folder = '/scratch/local1/m300382/icon_globe/'
input_file=folder+'ICON_*_3h.nc' # 3 hourly
# input_file=folder+'ICON_*[!3h].nc' # hourly
folder_images = folder 
chunks_size = 8 
processes = 4
figsize_x = 14 
figsize_y = 9

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

folder_glyph = '/home/mpim/m300382/icons_weather/yrno_png/'
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

def print_message(message):
    """Formatted print"""
    print(main.__file__+' : '+message)

def get_weather_icons(ww, time):
    from matplotlib._png import read_png
    """
    Get the path to a png given the weather representation 
    """
    weather = [WMO_GLYPH_LOOKUP_PNG[w.astype(int).astype(str)] for w in ww.values]
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

def get_coordinates(dataset):
    """Get the lat/lon coordinates from the dataset and convert them to degrees.
    I'm converting them again to an array since metpy does some weird things on 
    the array."""
    dataset['clon'].metpy.convert_units('degreeN')
    dataset['clat'].metpy.convert_units('degreeE')
    # We have to return an array otherwise Basemap 
    # will complain
    return(dataset['clon'].values, dataset['clat'].values)

def get_city_coordinates(city):
    """Get the lat/lon coordinates of a city given its name using geopy."""
    from geopy.geocoders import Nominatim
    geolocator =Nominatim(user_agent='meteogram')
    loc = geolocator.geocode(city)
    return(loc.longitude, loc.latitude)

def get_projection(lon, lat, projection="nh", countries=True, regions=False, labels=False):
    """Create the projection in Basemap and returns the x, y array to use it in a plot"""
    if projection=="nh":
        m = Basemap(projection='nsper',lon_0=-25,lat_0=50, resolution='l',satellite_height=4e6)
    elif projection=="us":
        m = Basemap(projection='nsper',lon_0=-100,lat_0=45, resolution='l',satellite_height=4e6)
        m.drawstates(linewidth=0.5, linestyle='solid', color='black', zorder=5)
    elif projection=="euratl":
        m = Basemap(projection='mill', llcrnrlon=-50, llcrnrlat=30, urcrnrlon=30, urcrnrlat=70,resolution='i')
    elif projection=="eur":
        m = Basemap(projection='cyl', llcrnrlon=-15, llcrnrlat=29, urcrnrlon=35, urcrnrlat=71,resolution='i')
    elif projection=="world":
        m = Basemap(projection='kav7',lon_0=0, resolution='c')
    elif projection=="nh_polar":
        m = Basemap(projection='npaeqd',boundinglat=30,lon_0=0,resolution='l')

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

    x, y = m(lon,lat)
    
    return(m, x, y)

def get_projection_cartopy(plt, lon, lat, projection="nh"):
    """Create the projection in cartopy and returns the x, y array to use it in a plot"""
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    if projection=="nh":
        proj = ccrs.NearsidePerspective(
                            central_latitude=50.,
                            central_longitude=-25.,
                            satellite_height=4e6)
    elif projection=="us":
        proj = ccrs.NearsidePerspective(
                            central_latitude=45.,
                            central_longitude=-100.,
                            satellite_height=4e6)
    elif projection=="world":
        proj = ccrs.Mollweide()

    ax = plt.axes(projection=proj)

    if projection!="world":
        ax.coastlines(resolution='50m')
        ax.add_feature(cfeature.BORDERS.with_scale('50m'), zorder=5)
    else:
        ax.coastlines(resolution='110m')
        ax.add_feature(cfeature.BORDERS.with_scale('110m'), zorder=5)

    if projection=="us":
        states_provinces = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none')
        ax.add_feature(states_provinces, edgecolor='gray')
    
    x, y, _ = proj.transform_points(ccrs.PlateCarree(), lon, lat).T
    
    return(ax, x, y)

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

# Annotation run, models 
def annotation_run(ax, time, loc='upper right',fontsize=8):
    """Put annotation of the run obtaining it from the
    time array passed to the function."""
    at = AnchoredText('Run %s'% time[0].strftime('%Y%m%d %H UTC'), 
                      prop=dict(size=fontsize), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    ax.add_artist(at)
    return(at)

def annotation(ax, text, loc='upper right',fontsize=8):
    """Put a general annotation in the plot."""
    at = AnchoredText('%s'% text, prop=dict(size=fontsize), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    ax.add_artist(at)
    return(at)

def annotation_forecast(ax, time, loc='upper left',fontsize=8):
    """Put annotation of the forecast time."""
    at = AnchoredText('Forecast for %s' % time.strftime('%A %d %b %Y at %H UTC'), 
                       prop=dict(size=fontsize), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    ax.add_artist(at)
    return(at)

def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=256):
    """Truncate a colormap by specifying the start and endpoint."""
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return(new_cmap)

def get_colormap(cmap_type):
    """Create a custom colormap."""
    colors_tuple = pd.read_csv('/home/mpim/m300382/icon_forecasts/cmap_%s.rgba' % cmap_type).values 
         
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
        colors_tuple = pd.read_csv('/home/mpim/m300382/icon_forecasts/cmap_prec.rgba').values    
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
