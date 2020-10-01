import xarray as xr 
import metpy.calc as mpcalc
from metpy.units import units
import numpy as np
from multiprocessing import Pool
from functools import partial
import os 
from utils import *
import sys
import Ngl
import copy

# The one employed for the figure name when exported 
variable_name = 'gph_500'

print_message('Starting script to plot '+variable_name)

# Get the projection as system argument from the call so that we can 
# span multiple instances of this script outside
if not sys.argv[1:]:
    print_message('Projection not defined, falling back to default (nh, us, world)')
    projections = ['nh','us','world']
else:    
    projections=sys.argv[1:]

def main():
    """In the main function we basically read the files and prepare the variables to be plotted.
    This is not included in utils.py as it can change from case to case."""
    dset, time, cum_hour  = read_dataset(variables=['T', 'FI'])

    # Select 850 hPa level using metpy
    temp_850 = dset['t'].metpy.sel(vertical=850 * units.hPa).load()
    temp_850.metpy.convert_units('degC')
    z_500 = dset['z'].metpy.sel(vertical=500 * units.hPa).load()
    gph_500 = mpcalc.geopotential_to_height(z_500)
    gph_500 = xr.DataArray(gph_500, coords=z_500.coords,
                           attrs={'standard_name': 'geopotential height',
                                  'units': gph_500.units})

    del z_500

    lon, lat = get_coordinates()

    for projection in projections:# This works regardless if projections is either single value or array

        # All the arguments that need to be passed to the plotting function
        args=dict(lon=lon, lat=lat,temp_850=temp_850.values, 
                gph_500=gph_500.values, time=time,
                 projection=projection, cum_hour=cum_hour)

        print_message('Pre-processing finished, launching plotting scripts')

        # plot_files(time[0:2], **args)
        dates = chunks(time, chunks_size)
        plot_files_param=partial(plot_files, **args)
        p = Pool(processes)
        p.map(plot_files_param, dates)

def plot_files(dates, **args):
    # Using args we don't have to change the prototype function if we want to add other parameters!
    res =  Ngl.Resources()
    res.nglDraw = False
    res.nglFrame = False
    res.sfXArray =  args['lon']
    res.sfYArray =  args['lat']
    resC = copy.deepcopy(res)

    res.mpFillOn =  False
    res.mpGridAndLimbOn =  False 
    res.mpProjection  =  "WinkelTripel"
    res.mpOutlineBoundarySets = "National"
    res.mpPerimOn =  False
    res.pmTickMarkDisplayMode = 'Never'
    resF = copy.deepcopy(res)

    resF.lbLabelBarOn = False
    resF.cnFillOn  =  True
    resF.cnFillMode = "RasterFill"
    resF.cnLinesOn =  False
    resF.cnLineLabelsOn =  False 
    resF.cnLevelSelectionMode = "ExplicitLevels"
    resF.cnLevels = np.arange(-35., 30., 1.)
    cmap_r  = Ngl.read_colormap_file("BkBlAqGrYeOrReViWh200")
    cmap_r[0,:] = 0.0
    resF.cnFillPalette = cmap_r

    resC.cnFillOn  =  False
    resC.cnLinesOn =  True
    resC.cnInfoLabelOn = False
    resC.cnLevelSelectionMode = "ExplicitLevels"
    resC.cnLevels = np.arange(4800., 5800., 70.)
    resC.cnLineThicknessF = 3
    resC.cnLineColor = "gray60"
    resC.cnLineLabelFontHeightF = 0.004
    resC.cnLineLabelDensityF = 1.5

    for date in dates:
        i = np.argmin(np.abs(date - args['time']))
        filename = subfolder_images[args['projection']]+'/'+variable_name+'_%s.png' % args['cum_hour'][i]
        wks = Ngl.open_wks("png",filename)

        plot_lines = Ngl.contour(wks,args['gph_500'][i], resC)
        plot_contourf = Ngl.contour_map(wks,args['temp_850'][i], resF)

        Ngl.overlay(plot_contourf, plot_lines)
        Ngl.draw(plot_contourf)
        Ngl.frame(wks)

    del resF
    del resC
    del res 

if __name__ == "__main__":
    import time
    start_time=time.time()
    main()
    elapsed_time=time.time()-start_time
    print_message("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
