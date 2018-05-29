load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/cd_string.ncl"

begin
; Open model level output file

fils = systemfunc ("ls /scratch/local1/m300382/icon_globe/*.nc") ; file paths
f_pres    = addfiles (fils, "r")  
ListSetType (f_pres, "cat")

plot_description="Maximum wind speed at 10m (m/s, colors) and MSLP (black contours, hPa)"

RAD2DEG = get_r2d("float")

wind=f_pres[:]->10fg3(:,0,:)
mslp=f_pres[:]->prmsl

lon = f_pres[:]->clon * RAD2DEG 
lat = f_pres[:]->clat * RAD2DEG
time= f_pres[:]->time

date_string=time/60
run_time=str_sub_str(time@units,"minutes since ","")
run_string="Run: "+run_time

delete([/fils, f_pres/])

mslp=mslp/100.
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

ResC2=ResC
ResC2@cnFillOn = False
ResC2@cnLinesOn= True
ResC@cnFillOn = True ; do color fill
ResC@cnFillMode = "rasterfill"
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
ResC@mpCenterLonF               = 260.0       ; choose center lon
ResC@mpCenterLatF               = 45.         ; choose center lat
ResC@mpSatelliteDistF           = 2.         ; choose satellite view
;SATELLITE 

ResC@mpGeophysicalLineThicknessF = 1
ResC@mpGeophysicalLineColor ="black"
ResC@mpOutlineBoundarySets     = "geophysicalandusstates"; turn on states
; ResC@mpDataBaseVersion         = "mediumres"             ; select database
ResC@mpDataSetName             = "Earth..2"    
ResC@mpFillOn = True 
ResC@mpOutlineOn = True  
ResC@pmTickMarkDisplayMode = True
; ResC2@cnLevelSelectionMode = "ManualLevels"
; ResC2@cnMinLevelValF = round(min(geop_850),0)+10
; ResC2@cnMaxLevelValF = round(max(geop_850),0)+10
ResC2@cnLevelSpacingF = 7
ResC2@cnInfoLabelOn = False  
ResC2@cnLineThicknessF = 3
ResC2@cnLineColor = "gray70"
ResC2@cnLineLabelFontHeightF = 0.004
ResC2@cnLineLabelDensityF = 1.5
; ResC2@cnLabelMasking             = True        
ResC2@cnLineLabelBackgroundColor = "transparent"

ResC@lbLabelFontHeightF = 0.01
ResC@lbBoxEndCapStyle = "TriangleBothEnds"
cmap_r=read_colormap_file("wind_17lev")
cmap_r(0,:)=0.0
ResC@cnFillPalette= cmap_r
ResC@cnLevelSelectionMode = "ManualLevels"
ResC@cnMinLevelValF = 5
ResC@cnMaxLevelValF = 35 
ResC@cnLevelSpacingF = 1
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

do time_i=0,dimsizes(time)-1
   ResC@gsnCenterString= "Forecast for "+cd_string(time(time_i), "%d %c. %Y")+" at "+cd_string(time(time_i), "%H:%M")+" UTC"
   wks = gsn_open_wks("png","us/winds10m_"+date_string(time_i))

   plot = gsn_csm_contour_map(wks,wind(time_i,:),ResC)
   over = gsn_csm_contour(wks,mslp(time_i,:),ResC2)

   text=gsn_create_text(wks, run_string, txres)
   run_annotation=gsn_add_annotation(plot, text, amres)

   text2=gsn_create_text(wks, plot_description, txres)
   description=gsn_add_annotation(plot, text2, amres2)

   overlay(plot, over)
   draw(plot)
   frame(wks)

   ; if time_i.eq.1 then
   ;     print("FIRST PLOT DONE in "+get_cpu_time()+"s") 
   ; end if 
end do
end
