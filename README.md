# icon_globe
Download and plot ICON data over the global domain.

In the following repository I include a fully-functional suite of scripts 
needed to download, merge and plot data from the ICON model,
which is freely available at https://opendata.dwd.de/weather/.

The main script to be called (possibly through cronjob) is `copy_data.run`. 
There, the current run version is determined, and files are downloaded from the DWD server.
CDO is used to merge the files. At the end of the process one single NETCDF file with all the variables 
and timesteps is obtained.

## Parallelized donwload of data 
Downloading and merging the data is one of the process that can take more time depending on the connection.
For this reason this is fully parallelized making use of the GNU `parallel` utility. 
```bash
# 2-D variables
variables=("PMSL" "CLCT" "TOT_PREC" "VMAX_10M" "RAIN_CON" "RAIN_GSP" "SNOW_CON" "SNOW_GSP" "T_2M" "TD_2M" "WW" "CAPE_CON")
${parallel} -j 8 download_merge_2d_variable_icon_globe ::: "${variables[@]}"

# 3-D variables on pressure levels
variables=("T" "FI" "RELHUM" "U" "V")
${parallel} -j 16 download_merge_3d_variable_icon_globe ::: "${variables[@]}"
``` 
The list of variables to download using such parallelization is provided as bash array. 2-D and 3-D variables have different
routines: these are all defined in the common library `functions_download_dwd.sh`. The link to the DWD opendata server is also defined in this file. 

## Parallelized plotting
Plotting of the data is done using Python, but anyone could potentially use other software. This is also parallelized
given that plotting routines are the most expensive part of the whole script and can take a lot of time (up to 2 hours
depending on the load). 
This is make especially easier by the 
fact that the plotting scripts can be given as argument the projection so we can parallelize across multiple projections
and script files, for example:
```bash
scripts=("plot_jetstream.py" "plot_rain_acc.py" "plot_clouds.py" "plot_geop_500.py" "plot_mslp_wind.py" "plot_thetae.py")
projections=("world" "nh" "us")

${parallel} -j 6 ${python} ::: "${scripts[@]}" ::: "${projections[@]}"
``` 
Note that the data are processed using the original icosahedral grid.

## Upload of the pictures
PNG pictures are uploaded to a FTP server defined in `ncftp` bookmarks.
