# icon_globe
- Parallelize downloading and extracting of data by writing a function which is then called in the background
- Try to see whether it's faster to call `open_mfdataset` and load variables or instead read the datasets with `open_dataset` and then merge them together afterwards. 
- Check if `psyplot` is faster in doing the plot instead than plain `matplotlib` with `tricontourf`. 
- Move processing of data in the projection loop after the data has being subsetted 