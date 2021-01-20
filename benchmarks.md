Some benchmarks.

### Remapping before plotting
Remapping all the files before plotting takes the following amount on Ekman with 16 CPUs:
- ~5 seconds for 2D variables
- ~40 seconds for 3D variables
which means about 4 minutes in total. This using the weights.
 
Then plotting 
- Original grid, full forecast every 3 hours, NH projection -> 2min 10s 
- Remapped (0.15 deg) grid, full forecast every 3 hours, NH projection -> 1min
- Original grid, full forecast every 3 hours, euratl projection -> 35s (with subsetting)
- Remapped (0.15 deg) grid, full forecast every 3 hours, euratl projection -> 13s (with subsetting)
- Original grid, full forecast every 3 hours, world projection -> 15min 25s
- Remapped (0.15 deg) grid, full forecast every 3 hours, world projection -> 2min 14s

Of course with the remap output we can do more with the output like putting H/L symbols and other stuff. 
