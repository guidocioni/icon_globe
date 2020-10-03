#Given a variable name and year-month-day-run as environmental variables download and merges the variable
################################################
listurls() {
	filename="$1"
	url="$2"
  	wget --spider -r -nH -np -nv -nd --reject "index.html" --cut-dirs=3 \
		-A $filename.bz2 $url 2>&1\
		| grep -Eo '(http|https)://(.*).bz2'
}
#
get_and_extract_one() {
  url="$1"
  file=`basename $url | sed 's/\.bz2//g'`
  wget -q -O - "$url" | bzip2 -dc > "$file"
}
export -f get_and_extract_one
##############################################
download_merge_2d_variable_icon_globe()
{
	filename="icon_global_icosahedral_single-level_${year}${month}${day}${run}_*_${1}.grib2"
	url="https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${1,,}/"
	listurls $filename $url | parallel get_and_extract_one {}
	cdo -f nc copy -mergetime ${filename} ${1}_${year}${month}${day}${run}_global.nc
	rm ${filename}
}
export -f download_merge_2d_variable_icon_globe
################################################
download_merge_3d_variable_icon_globe()
{
	# Parallelize this part by getting a file list and dividing into chunks ##############
	filename="icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${1}.grib2"
	url="https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${1,,}/"
	listurls $filename $url | parallel get_and_extract_one {}
	#######################
	# To select only some of the levels
	# for level in "300" "500" "700" "850" "950" "1000" ; do
	# 	(
	# 	 cdo -f nc copy -mergetime icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${level}_${1}.grib2 icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_${level}_${1}.nc
	# 	) &
	# done
	# wait
	# ########
	# # First sort files numerically otherwise the levels get screwed up
	# files_to_merge=`ls -v icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${1}.nc` 
	# cdo merge ${files_to_merge} ${1}_${year}${month}${day}${run}_global.nc
	# rm icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${1}.nc
	cdo merge ${filename} ${1}_${year}${month}${day}${run}_global.grib2
	rm ${filename}
	cdo -f nc copy ${1}_${year}${month}${day}${run}_global.grib2 ${1}_${year}${month}${day}${run}_global.nc
	rm ${1}_${year}${month}${day}${run}_global.grib2
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
	url="https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${1,,}/"
	listurls $filename $url | parallel get_and_extract_one {}
	cdo -f nc copy -mergetime ${filename} ${1}_${year}${month}${day}${run}_global.nc
	rm ${filename}
}
export -f download_merge_soil_variable_icon_globe
