import metpy.calc as mpcalc
import xarray as xr
from metpy.units import units
from utils import *


# def compute_potential_vorticity(dset, tvar='t', pres=350, uvar='u', vvar='v'):
#     theta = mpcalc.potential_temperature(pres * units.hPa)

def compute_spacing(dset):
    dx, dy = mpcalc.lat_lon_grid_deltas(dset['lon'],
                                        dset['lat'])
    
    dx = xr.DataArray(dx.magnitude,
             dims=['y1', 'x1'],
           attrs={'standard_name': 'x grid spacing',
                  'units': dx.units},
                       name='dx')
    dy = xr.DataArray(dy.magnitude,
             dims=['y2', 'x2'],
           attrs={'standard_name': 'y grid spacing',
                  'units': dx.units},
                       name='dy')
    
    out = xr.merge([dset, dx, dy])
    out.attrs = dset.attrs
    
    return out


def compute_theta(dset, tvar='t'):
    pres =  dset['plev'].metpy.unit_array
    theta = mpcalc.potential_temperature(pres[:, None, None], dset[tvar]).metpy.dequantify()
    
    theta = xr.DataArray(theta.values,
                           coords= dset[tvar].coords,
                           attrs={'standard_name': 'Potential Temperature',
                                  'units': theta.units},
                            name='theta')

    out = xr.merge([dset, theta])
    out.attrs = dset.attrs

    return out


# Only call this on a time-subset dataset!! 
def compute_pv(dset):
    dx = dset['dx'].values[:] * units(str(dset['dx'].units))
    dy = dset['dy'].values[:] * units(str(dset['dy'].units))
    lats = dset['lat'].metpy.unit_array
    pres =  dset['plev'].metpy.unit_array
    theta = dset['theta'].values[:] * units(str(dset['theta'].units))
    pv = mpcalc.potential_vorticity_baroclinic(potential_temperature=theta,
                                               pressure=pres[:, None, None],
                                               u=dset['u'],
                                               v=dset['v'],
                                               dx=dx[None, :, :],
                                               dy=dy[None, :, :],
                                               latitude=lats[None, :, None]
                                               )
    
    pv = xr.DataArray(np.array(pv),
                       coords=dset['u'].coords,
                       attrs={'standard_name': 'Potential Vorticity',
                              'units': pv.units},
                       name='pv')
    
    out = xr.merge([dset, pv])
    out.attrs = dset.attrs

    return out

    
def compute_geopot_height(dset, zvar='z', level=None):
    if level:
        zlevel = dset[zvar].sel(plev=level)
    else:
        zlevel = dset[zvar]
    gph = mpcalc.geopotential_to_height(zlevel).metpy.dequantify()
    gph = xr.DataArray(gph.values,
                       coords=zlevel.coords,
                       attrs={'standard_name': 'geopotential height',
                              'units': gph.units},
                       name='geop')

    return xr.merge([dset, gph])


def compute_thetae(dset, tvar='t', rvar='r'):
    rh = mpcalc.dewpoint_from_relative_humidity(dset[tvar],
                                                dset[rvar] / 100.)
    theta_e = mpcalc.equivalent_potential_temperature(850 * units.hPa,
                                                      dset[tvar],
                                                      rh)
    theta_e = theta_e.metpy.convert_units('degC').metpy.dequantify()
    theta_e = xr.DataArray(theta_e.values,
                           coords= dset[tvar].coords,
                           attrs={'standard_name': 'Equivalent potential temperature',
                                  'units': theta_e.units},
                            name='theta_e')

    return xr.merge([dset, theta_e])


def compute_snow_change(dset, snowvar='sde'):
    hsnow_acc = dset[snowvar]
    hsnow = (hsnow_acc - hsnow_acc[0, :, :])
    hsnow = hsnow.where((hsnow > 0.5) | (hsnow < -0.5))

    hsnow = xr.DataArray(hsnow,
                           coords= hsnow_acc.coords,
                           attrs={'standard_name': 'Snow accumulation since beginning',
                                  'units': hsnow_acc.units},
                            name='snow_increment')

    out = xr.merge([dset, hsnow])
    out.attrs = dset.attrs

    return out


def compute_rain_snow_change(dset):
    try:
        rain_acc = dset['RAIN_GSP'] + dset['RAIN_CON']
    except:
        rain_acc = dset['RAIN_GSP']
    try:
        snow_acc = dset['SNOW_GSP'] + dset['SNOW_CON']
    except:
        snow_acc = dset['SNOW_GSP']

    rain = (rain_acc - rain_acc[0, :, :])
    snow = (snow_acc - snow_acc[0, :, :])

    rain = xr.DataArray(rain, name='rain_increment')
    snow = xr.DataArray(snow, name='snow_increment')

    out = xr.merge([dset, rain, snow])
    out.attrs = dset.attrs

    return out


def compute_wind_speed(dset, uvar='u', vvar='v'):
    wind = mpcalc.wind_speed(dset[uvar], dset[vvar]).metpy.convert_units('kph').metpy.dequantify()
    wind = xr.DataArray(wind, coords=dset[uvar].coords,
                           attrs={'standard_name': 'wind intensity',
                                  'units': wind.units},
                                  name='wind_speed')

    return xr.merge([dset, wind])


def compute_rate(dset):
    '''Given an accumulated variable compute the step rate'''
    try:
        rain_acc = dset['RAIN_GSP'] + dset['RAIN_CON']
    except:
        rain_acc = dset['RAIN_GSP']
    try:
        snow_acc = dset['SNOW_GSP'] + dset['SNOW_CON']
    except:
        snow_acc = dset['SNOW_GSP']

    rain = rain_acc.load().differentiate(coord="time", datetime_unit="h")
    snow = snow_acc.load().differentiate(coord="time", datetime_unit="h")

    rain = xr.DataArray(rain, name='rain_rate')
    snow = xr.DataArray(snow, name='snow_rate')

    out = xr.merge([dset, rain, snow])
    out.attrs = dset.attrs

    return out


def compute_soil_moisture_sat(dset, projection):
    proj_options = proj_defs[projection]
    saturation = xr.open_dataset(soil_saturation_file)['soil_saturation']
    saturation = saturation.assign_coords({"lon": (((saturation.lon + 180) % 360) - 180)})
    saturation = saturation.sel(lat=slice(proj_options['llcrnrlat'],
                                          proj_options['urcrnrlat']),
                                lon=slice(proj_options['llcrnrlon'],
                                          proj_options['urcrnrlon']))

    w_so = dset['W_SO']

    rho_w = 1000.
    w_so = w_so / (0.03 * 2 * rho_w)

    w_so_sat = (w_so.values[:, :, :] / saturation.values[None, :, :]) * 100.

    w_so_sat = xr.DataArray(w_so_sat, coords=w_so.coords,
                           attrs={'standard_name': 'Soil moisture saturation',
                                  'units': '%'},
                            name='w_so_sat')

    # Fix weird points with ice/rock
    w_so_sat = w_so_sat.where(w_so != 0, 0.)

    out = xr.merge([dset, w_so_sat])
    out.attrs = dset.attrs

    return out
