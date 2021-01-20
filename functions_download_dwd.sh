#Given a variable name and year-month-day-run as environmental variables download and merges the variable
################################################
listurls() {
	filename="$1"
	url="$2"
	wget -qO- $url | grep -Eoi '<a [^>]+>' | \
	grep -Eo 'href="[^\"]+"' | \
	grep -Eo $filename | \
	xargs -I {} echo "$url"{}
}
export -f listurls
#
get_and_extract_one() {
  url="$1"
  file=`basename $url | sed 's/\.bz2//g'`
  if [ ! -f "$file" ]; then
  	wget -t 2 -q -O - "$url" | bzip2 -dc > "$file"
  fi
}
export -f get_and_extract_one
##############################################
download_merge_2d_variable_icon_globe()
{
	filename="icon_global_icosahedral_single-level_${year}${month}${day}${run}_*_${1}.grib2"
	filename_grep="icon_global_icosahedral_single-level_${year}${month}${day}${run}_(${hours_download})_${1}.grib2.bz2"
	url="https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${1,,}/"
	echo "folder: ${url}"
	echo "files: ${filename}"
	if [ ! -f "${1}_${year}${month}${day}${run}_global.nc" ]; then
		listurls $filename_grep $url | parallel -j 10 get_and_extract_one {}
		find ${filename} -empty -type f -delete # Remove empty files
		cdo -f nc copy -mergetime ${filename} ${1}_${year}${month}${day}${run}_global.nc
		rm ${filename}
	fi
	if [ "$REMAP" = true ]; then
		mkdir -p ${MODEL_DATA_FOLDER}remap
		echo "Remapping the output as requested"
		cdo -P 8 remap,"${HOME_FOLDER}/grids/target_grid_world_0150.txt","${HOME_FOLDER}/grids/weights_icogl2world_0150.nc" \
			-setgrid,"${HOME_FOLDER}/grids/icon_grid_0026_R03B07_G.nc" "${1}_${year}${month}${day}${run}_global.nc" "remap/${1}_${year}${month}${day}${run}_global.nc"
	fi
}
export -f download_merge_2d_variable_icon_globe
################################################
download_merge_3d_variable_icon_globe()
{
	filename="icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_*_${1}.grib2"
	filename_grep="icon_global_icosahedral_pressure-level_${year}${month}${day}${run}_(${hours_download})_(1000|900|850|700|600|500|300|250|150|50)_${1}.grib2.bz2"
	url="https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${1,,}/"
	if [ ! -f "${1}_${year}${month}${day}${run}_global.nc" ]; then
		listurls $filename_grep $url | parallel -j 10 get_and_extract_one {}
		find ${filename} -empty -type f -delete # Remove empty files
		cdo merge ${filename} ${1}_${year}${month}${day}${run}_global.grib2
		rm ${filename}
		cdo -f nc copy ${1}_${year}${month}${day}${run}_global.grib2 ${1}_${year}${month}${day}${run}_global.nc
		rm ${1}_${year}${month}${day}${run}_global.grib2
	fi
	if [ "$REMAP" = true ]; then
		mkdir -p ${MODEL_DATA_FOLDER}remap
		echo "Remapping the output as requested"
		cdo -P 8 remap,"${HOME_FOLDER}/grids/target_grid_world_0150.txt","${HOME_FOLDER}/grids/weights_icogl2world_0150.nc" \
			-setgrid,"${HOME_FOLDER}/grids/icon_grid_0026_R03B07_G.nc" "${1}_${year}${month}${day}${run}_global.nc" "remap/${1}_${year}${month}${day}${run}_global.nc"
	fi
}
export -f download_merge_3d_variable_icon_globe
################################################
# Download grid and topography, the grid we need it for ICON global
download_invariant_icon_globe()
{
	for invar_variable in "HSURF" "CLAT" "CLON" ; do
		filename="icon_global_icosahedral_time-invariant_${year}${month}${day}${run}_${invar_variable}.grib2"
		wget -r -nH -np -nv -nd --reject "index.html*" --cut-dirs=3 -A "${filename}.bz2" "https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${invar_variable,,}/"
		bzip2 -d ${filename}.bz2 
		cdo -f nc copy ${filename} invariant_${invar_variable}_${year}${month}${day}${run}_global.nc
		rm ${filename}
	done
	files_to_merge=`ls -v invariant_*_${year}${month}${day}${run}_global.nc`
	cdo merge ${files_to_merge} invariant_${year}${month}${day}${run}_global.nc
	rm ${files_to_merge}
	if [ "$REMAP" = true ]; then
		mkdir -p ${MODEL_DATA_FOLDER}remap
		echo "Remapping the output as requested"
		cdo -P 8 remap,"${HOME_FOLDER}/grids/target_grid_world_0150.txt","${HOME_FOLDER}/grids/weights_icogl2world_0150.nc" \
			-setgrid,"${HOME_FOLDER}/grids/icon_grid_0026_R03B07_G.nc" "invariant_${year}${month}${day}${run}_global.nc" "remap/invariant_${year}${month}${day}${run}_global.nc"
	fi
}
export -f download_invariant_icon_globe
################################################
download_merge_soil_variable_icon_globe()
{
	filename="icon_global_icosahedral_soil-level_${year}${month}${day}${run}_*_3_${1}.grib2"
	filename_grep="icon_global_icosahedral_soil-level_${year}${month}${day}${run}_(${hours_download})_3_${1}.grib2.bz2"
	url="https://opendata.dwd.de/weather/nwp/icon/grib/${run}/${1,,}/"
	if [ ! -f "${1}_${year}${month}${day}${run}_global.nc" ]; then
		listurls $filename_grep $url | parallel -j 10 get_and_extract_one {}
		find ${filename} -empty -type f -delete # Remove empty files
		cdo -f nc copy -mergetime ${filename} ${1}_${year}${month}${day}${run}_global.nc
		rm ${filename}
	fi
	if [ "$REMAP" = true ]; then
		mkdir -p ${MODEL_DATA_FOLDER}remap
		echo "Remapping the output as requested"
		cdo -P 8 remap,"${HOME_FOLDER}/grids/target_grid_world_0150.txt","${HOME_FOLDER}/grids/weights_icogl2world_0150.nc" \
			-setgrid,"${HOME_FOLDER}/grids/icon_grid_0026_R03B07_G.nc" "${1}_${year}${month}${day}${run}_global.nc" "remap/${1}_${year}${month}${day}${run}_global.nc"
	fi
}
export -f download_merge_soil_variable_icon_globe
