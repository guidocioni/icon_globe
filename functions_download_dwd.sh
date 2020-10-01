#Given a variable name and year-month-day-run as environmental variables download and merges the variable
download_merge_2d_variable_icon_globe()
{
	filename="icon_global_icosahedral_single-level_${year}${month}${day}${run}_*_${1}.grib2"
	wget -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${1,,}/"
	echo 'Extracting files'
	bzip2 -d ${filename}.bz2 
	cdo -f nc copy -mergetime ${filename} ${1}_${year}${month}${day}${run}_global.nc
	rm ${filename}
}
export -f download_merge_2d_variable_icon_globe
################################################
download_merge_3d_variable_icon_globe()
{
	# Parallelize this part by getting a file list and dividing into chunks ##############
	filename="icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${1}.grib2"
	wget -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${1,,}/"
	echo 'Extracting files'
	bzip2 -d ${filename}.bz2
	#######################
	# Parallelize this loop
	for level in "300" "500" "700" "850" "950" "1000" ; do
		(
		 cdo -f nc copy -mergetime icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${level}_${1}.grib2 icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_${level}_${1}.nc
		 rm icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${level}_${1}.grib2
		) &
	done
	wait
	########
	# First sort files numerically otherwise the levels get screwed up
	files_to_merge=`ls -v icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${1}.nc` 
	cdo merge ${files_to_merge} ${1}_${year}${month}${day}${run}_global.nc
	rm icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${1}.nc
}
export -f download_merge_3d_variable_icon_globe
################################################
# Download grid and topography, the grid we need it for ICON global
download_invariant_icon_globe()
{
	for invar_variable in "HSURF" "CLAT" "CLON" "ELAT" "ELON" ; do
		filename="icon_global_icosahedral_time-invariant_${year}${month}${day}${run}_${invar_variable}.grib2"
		wget -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${invar_variable,,}/"
		bzip2 -d ${filename}.bz2 
		cdo -f nc copy ${filename} invariant_${invar_variable}_${year}${month}${day}${run}_global.nc
		rm ${filename}
	done
	files_to_merge=`ls -v invariant_*_${year}${month}${day}${run}_global.nc`
	cdo merge ${files_to_merge} invariant_${year}${month}${day}${run}_global.nc
	rm ${files_to_merge}
}
export -f download_invariant_icon_globe
################################################
download_merge_soil_variable_icon_globe()
{
	filename="icon_global_icosahedral_soil-level_${year}${month}${day}${run}_*_3_${1}.grib2"
	wget -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/nwp/icon-eu/grib/${run}/${1,,}/"
	echo 'Extracting files'
	bzip2 -d ${filename}.bz2
	cdo -f nc copy -mergetime ${filename} ${1}_${year}${month}${day}${run}_global.nc
	rm ${filename}
}
export -f download_merge_soil_variable_icon_globe
