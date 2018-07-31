load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/cd_string.ncl"

begin
; Open model level output file

fils = systemfunc ("ls /scratch/local1/m300382/icon_globe/ICON_*_3h.nc") ; file paths
f_rain    = addfiles (fils, "r")  
ListSetType (f_rain, "cat")

plot_description="Accumulated precipitation (mm) since run start"

RAD2DEG = get_r2d("float")


 tot_prec=f_rain[:]->tp
 mslp=f_rain[:]->prmsl

lon = f_rain[:]->clon * RAD2DEG 
lat = f_rain[:]->clat * RAD2DEG
 time= f_rain[:]->time 

date_string=time/60
run_time=str_sub_str(time@units,"minutes since ","")
run_string="Run: "+run_time

mslp = mslp/100.

 delete([/fils, f_rain/])

; create plot

 ResC = True
 ResC@gsnDraw = False
 ResC@gsnFrame = False
 ResC@gsnAddCyclic = False  
 ResC@gsnMaximize   = True         ; Maximize plot in frame.
 ResC@gsnLeftString = ""
 ResC@gsnRightString = ""
 ResC@gsnStringFontHeightF=0.01
 ResC@cnFillMode = "RasterFill"
 ResC@sfXArray = lon 
 ResC@sfYArray = lat 

 ResC2=ResC

 ResC@cnFillOn = True ; do color fill
 ResC@cnLinesOn=False

ResC@tmXBBorderOn      = False
ResC@tmXBOn            = False
ResC@tmXTBorderOn      = False
ResC@tmXTOn            = False
ResC@tmYLBorderOn      = False
ResC@tmYLOn            = False
ResC@tmYRBorderOn      = False
ResC@tmYROn            = False

;SATELLITE
ResC@mpProjection               = "Satellite" ; choose map projection
ResC@mpCenterLonF               = 330.0       ; choose center lon
ResC@mpCenterLatF               = 50.0        ; choose center lat
ResC@mpSatelliteDistF           = 3.0         ; choose satellite view
;SATELLITE 

ResC@mpGeophysicalLineThicknessF = 2
ResC@mpGeophysicalLineColor ="black"
ResC@mpDataSetName         = "Earth..4"     
ResC@mpFillOn = True 
ResC@mpOutlineOn = True  
ResC@pmTickMarkDisplayMode = True
 ; ResC@mpOutlineOn = True
 ResC@tmXBLabelFontHeightF = 0.01

 ResC@cnLevelSelectionMode = "ExplicitLevels"
 ResC@cnLevels = (/5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 150, 200, 250/)

cmap_r              = read_colormap_file("prcp_3")
cmap_r(0:1,:)=0.0
ResC@cnFillPalette = cmap_r

ResC@lbOrientation = "Vertical"
ResC@pmLabelBarWidthF = 0.04
ResC@pmLabelBarOrthogonalPosF = 0.
ResC@lbLabelFontHeightF = 0.005

ResC@gsnLeftString = "ICON"
ResC@gsnRightString = "Copyright DWD"

ResC2@cnLevelSelectionMode = "ManualLevels"
ResC2@cnMinLevelValF = round(min(mslp), 0)
ResC2@cnMaxLevelValF = round(max(mslp), 0)
ResC2@cnInfoLabelOn = False  
ResC2@cnLevelSpacingF = 7
ResC2@cnLineThicknessF = 3
ResC2@cnLineColor = "gray50"
ResC2@cnLineLabelFontHeightF = 0.004
ResC2@cnLineLabelDensityF = 1.5
; ResC2@cnLabelMasking             = True        
ResC2@cnLineLabelBackgroundColor = "transparent"

txres                       = True
txres@txPerimOn             = True
txres@txBackgroundFillColor = "White"
txres@txFontHeightF         = 0.011

amres=True 
amres@amParallelPosF   = -0.5    ; This is the right edge of the plot.
amres@amOrthogonalPosF = 0.5    ; This is the bottom edge of the plot.
amres@amJust = "BottomLeft"

amres2=True 
amres2@amParallelPosF   = -0.5    ; This is the right edge of the plot.
amres2@amOrthogonalPosF = -0.5    ; This is the bottom edge of the plot.
amres2@amJust = "TopLeft"

 do time_i=1,dimsizes(time)-1
 ResC@gsnCenterString= "Forecast for "+cd_string(time(time_i), "%d %c. %Y")+" at "+cd_string(time(time_i), "%H:%M")+" UTC"
 wks = gsn_open_wks("png","precip_acc_"+date_string(time_i))
 
  plot=gsn_csm_contour_map(wks, tot_prec(time_i,:), ResC)
  over = gsn_csm_contour(wks,mslp(time_i,:),ResC2)

   text=gsn_create_text(wks, plot_description, txres)
   description=gsn_add_annotation(plot, text, amres)
   text2=gsn_create_text(wks, run_string, txres)
   run_annotation=gsn_add_annotation(plot, text2, amres2)

   overlay(plot, over)

 draw(plot)
 frame(wks)
end do



end
