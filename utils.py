from mpl_toolkits.basemap import Basemap  # import Basemap matplotlib toolkit
import numpy as np
from matplotlib.offsetbox import AnchoredText
import matplotlib.colors as colors
import metpy.calc as mpcalc
from metpy.units import units

folder = '/scratch/local1/m300382/icon_globe/'
input_file=folder+'ICON_*_3h.nc' # 3 hourly
# input_file=folder+'ICON_*[!3h].nc' # hourly
folder_images = folder 
chunks_size = 10 
processes = 10
figsize_x = 16 
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

def get_coordinates(dataset):
    """Get the lat/lon coordinates from the dataset and convert them to degrees.
    I'm converting them again to an array since metpy does some weird things on 
    the array."""
    dataset['clon'].metpy.convert_units('degreeN')
    dataset['clat'].metpy.convert_units('degreeE')
    # We have to return an array otherwise Basemap 
    # will complain
    return(dataset['clon'].values, dataset['clat'].values)

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

    m.drawcoastlines(linewidth=0.5, linestyle='solid', color='black', zorder=5)
    if countries:
        m.drawcountries(linewidth=0.5, linestyle='solid', color='black', zorder=5)
    if labels:
        m.drawparallels(np.arange(-90.0, 90.0, 10.), linewidth=0.2, color='white',
            labels=[True, False, False, True], fontsize=7)
        m.drawmeridians(np.arange(0.0, 360.0, 10.), linewidth=0.2, color='white',
            labels=[True, False, False, True], fontsize=7)

    x, y = m(lon,lat)
    return(m, x, y)

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

def annotation(ax, text, loc='upper right',fontsize=8):
    """Put a general annotation in the plot."""
    at = AnchoredText('%s'% text, prop=dict(size=fontsize), frameon=True, loc=loc)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.1")
    ax.add_artist(at)

def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=256):
    """Truncate a colormap by specifying the start and endpoint."""
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap

def get_colormap(cmap_type, n_colors=64):
    """Create a custom colormap."""
    if cmap_type == "winds":
        colors_tuple = np.array([[1.        , 1.        , 1.        , 1.        ],
                                 [0.9372549 , 0.96078431, 0.81960784, 1.        ],
                                 [0.90980392, 0.95686275, 0.62745098, 1.        ],
                                 [0.6627451 , 0.80784314, 0.39607843, 1.        ],
                                 [0.88627451, 0.92941176, 0.09019608, 1.        ],
                                 [0.99607843, 0.92941176, 0.00392157, 1.        ],
                                 [1.        , 0.92941176, 0.50588235, 1.        ],
                                 [0.95686275, 0.81960784, 0.49803922, 1.        ],
                                 [0.9254902 , 0.65098039, 0.27843137, 1.        ],
                                 [0.90196078, 0.55294118, 0.23921569, 1.        ],
                                 [0.85882353, 0.48627451, 0.21960784, 1.        ],
                                 [0.94509804, 0.02352941, 0.24313725, 1.        ],
                                 [0.91372549, 0.33333333, 0.63921569, 1.        ],
                                 [0.60392157, 0.43921569, 0.65882353, 1.        ],
                                 [0.39215686, 0.43921569, 0.97254902, 1.        ],
                                 [0.49803922, 0.58823529, 0.99607843, 1.        ],
                                 [0.55686275, 0.69803922, 1.        , 1.        ]])
         
    cmap = colors.LinearSegmentedColormap.from_list(cmap_type, colors_tuple, n_colors)
    return(cmap)

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
        except ValueError:
            print('WARNING: Collection is empty')
