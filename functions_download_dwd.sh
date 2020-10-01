#Given a variable name and year-month-day-run as environmental variables download and merges the variable
parallelized_extraction(){
	# You need to pass a glob patter which will be tested for files
	until [ `ls -1 ${1}.bz2 2>/dev/null | wc -l ` -gt 0 ]; do
	     sleep 1
	done
	# 
	while [ `ls -1 ${1}.bz2 2>/dev/null | wc -l ` -gt 0 ]; do
		ls ${1}.bz2| parallel -j+0 bzip2 -d '{}' 
	    sleep 1
	done
}
download_merge_2d_variable_icon_globe()
{
	filename="icon_global_icosahedral_single-level_${year}${month}${day}${run}_*_${1}.grib2"
	wget -b -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${1,,}/"
	parallelized_extraction ${filename}
	cdo -f nc copy -mergetime ${filename} ${1}_${year}${month}${day}${run}_global.nc
	rm ${filename}
}
export -f download_merge_2d_variable_icon_globe
################################################
download_merge_3d_variable_icon_globe()
{
	# Parallelize this part by getting a file list and dividing into chunks ##############
	filename="icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${1}.grib2"
	wget -b -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${1,,}/"
	parallelized_extraction ${filename}
	#######################
	for level in "300" "500" "700" "850" "950" "1000" ; do
		(
		 cdo -f nc copy -mergetime icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${level}_${1}.grib2 icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_${level}_${1}.nc
		) &
	done
	wait
	########
	# First sort files numerically otherwise the levels get screwed up
	files_to_merge=`ls -v icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${1}.nc` 
	cdo merge ${files_to_merge} ${1}_${year}${month}${day}${run}_global.nc
	rm icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${1}.nc
	rm ${filename}
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
	wget -b -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/nwp/icon-eu/grib/${run}/${1,,}/"
	parallelized_extraction ${filename}
	cdo -f nc copy -mergetime ${filename} ${1}_${year}${month}${day}${run}_global.nc
	rm ${filename}
}
export -f download_merge_soil_variable_icon_globe
