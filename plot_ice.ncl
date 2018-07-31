load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/cd_string.ncl"

begin
; Open model level output file

fils = systemfunc ("ls /scratch/local1/m300382/icon_globe/ICON_*_3h.nc") ; file paths
f_pres    = addfiles (fils, "r")  
ListSetType (f_pres, "cat")

invariant=addfile("/home/mpim/m300382/icon_globe/ICON_iko_invar_package_world_grid.nc", "r")

plot_description="Sea ice cover (fraction) and snow height (cm)"

RAD2DEG = get_r2d("float")
ice=f_pres[:]->ci
h_snow=f_pres[:]->sde 
lsm=invariant->lsm(0,:)

lon = f_pres[:]->clon * RAD2DEG 
lat = f_pres[:]->clat * RAD2DEG
time= f_pres[:]->time

h_snow=h_snow*100.
h_snow=mask(h_snow, lsm.eq.0, False)

date_string=tostring(cd_calendar(time, -3))
run_time=str_sub_str(time@units,"minutes since ","")
run_string="Run: "+run_time

delete([/fils, f_pres/])

; create plot

ResC = True
ResC@gsnDraw = False
ResC@gsnFrame = False
ResC@gsnMaximize   = True         ; Maximize plot in frame.
ResC@gsnLeftString=""
ResC@gsnRightString=""
ResC@gsnStringFontHeightF = 0.012
ResC@sfXArray = lon 
ResC@sfYArray = lat 
ResC@cnFillOn = True
ResC@cnFillMode = "rasterfill"
ResC@cnLinesOn = False 
ResC@tmXBBorderOn      = False
ResC@tmXBOn            = False
ResC@tmXTBorderOn      = False
ResC@tmXTOn            = False
ResC@tmYLBorderOn      = False
ResC@tmYLOn            = False
ResC@tmYRBorderOn      = False
ResC@tmYROn            = False

ResC2 = ResC 

;SATELLITE
ResC@mpProjection               = "Satellite" ; choose map projection
ResC@mpCenterLonF               = 330.0       ; choose center lon
ResC@mpCenterLatF               = 50.0        ; choose center lat
ResC@mpSatelliteDistF           = 3.0         ; choose satellite view
;SATELLITE 
ResC@mpGeophysicalLineThicknessF = 2
ResC@mpGeophysicalLineColor ="gray50"
ResC@mpDataSetName         = "Earth..4"     
ResC@mpFillOn = False 
ResC@pmTickMarkDisplayMode = True

ResC2@cnLevelSelectionMode = "ManualLevels"
ResC2@cnMinLevelValF = 10
ResC2@cnMaxLevelValF = 100
ResC2@cnLevelSpacingF = 10
ResC2@cnInfoLabelOn = False  
ResC2@lbBoxEndCapStyle = "TriangleBothEnds"
cmap_r              := read_colormap_file("precip_11lev")
cmap_r(0,3)         = 0.0    ; Fully transparent
ResC2@cnFillPalette = cmap_r

ResC@lbLabelFontHeightF = 0.01
ResC@lbBoxEndCapStyle = "TriangleBothEnds"
cmap_r              := read_colormap_file("seaice_1")
cmap_r(0,3)         = 0.0    ; Fully transparent
ResC@cnFillPalette = cmap_r
ResC@cnLevelSelectionMode = "ManualLevels"
ResC@cnMinLevelValF = 0
ResC@cnMaxLevelValF = 1 
ResC@cnLevelSpacingF = .1
ResC@lbOrientation = "Vertical"
ResC@pmLabelBarWidthF = 0.05
ResC@gsnLeftString = "ICON"
ResC@gsnRightString = "Copyright DWD"

txres                       = True
txres@txPerimOn             = True
txres@txBackgroundFillColor = "White"
txres@txFontHeightF         = 0.012
amres=True 
amres@amParallelPosF   = -0.5    
amres@amOrthogonalPosF = -0.5    
amres@amJust = "TopLeft"

amres2=True 
amres2@amParallelPosF   = -0.5    ; This is the right edge of the plot.
amres2@amOrthogonalPosF = 0.5    ; This is the bottom edge of the plot.
amres2@amJust = "BottomLeft"


do time_i=1,dimsizes(time)-1
   ResC@gsnCenterString= "Forecast for "+cd_string(time(time_i), "%d %c. %Y")+" at "+cd_string(time(time_i), "%H:%M")+" UTC"
   wks = gsn_open_wks("x11","ICON_globe_ice_"+date_string(time_i))

   plot = gsn_csm_contour_map(wks,ice(time_i,:),ResC)
   over = gsn_csm_contour(wks,h_snow(time_i,:),ResC2)

   text=gsn_create_text(wks, run_string, txres)
   run_annotation=gsn_add_annotation(plot, text, amres)

   text2=gsn_create_text(wks, plot_description, txres)
   description=gsn_add_annotation(plot, text2, amres2)

   overlay(plot, over)
   draw(plot)
   frame(wks)

end do
end
