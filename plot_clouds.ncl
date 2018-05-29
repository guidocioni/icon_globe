load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/cd_string.ncl"

begin
; Open model level output file

fils = systemfunc ("ls /scratch/local1/m300382/icon_globe/*.nc") ; file paths
f_pres    = addfiles (fils, "r")  
ListSetType (f_pres, "cat")

plot_description="Total cloud fraction (grey scale) and precipitation (color shades)"

RAD2DEG = get_r2d("float")

mslp=f_pres[:]->prmsl
clcm=f_pres[:]->CLCT

lon = f_pres[:]->clon * RAD2DEG 
lat = f_pres[:]->clat * RAD2DEG
time= f_pres[:]->time

 depth_snow=f_pres[:]->SNOW_CON + f_pres[:]->SNOW_GSP
 copy_VarMeta(f_pres[:]->SNOW_CON, depth_snow)

 tot_prec=f_pres[:]->RAIN_CON + f_pres[:]->RAIN_GSP
 copy_VarMeta(f_pres[:]->RAIN_CON, tot_prec)

date_string=time/60
run_time=str_sub_str(time@units,"minutes since ","")
run_string="Run: "+run_time

delete([/fils, f_pres/])

 rain = tot_prec 
 rain = 0.0

 delete(rain@units)
 
 do i=1,dimsizes(time)-1
    rain(i,:)=tot_prec(i,:)-tot_prec(i-1,:) 
 end do 

change_snow=depth_snow
change_snow=0

do i=1,dimsizes(time)-1
    change_snow(i,:)=depth_snow(i,:)-depth_snow(i-1,:)
end do 

change_snow=mask(change_snow, change_snow .le. 0.5, False)
mslp=mslp/100.
; create plot

ResC = True
ResC@gsnDraw = False
ResC@gsnFrame = False
ResC@gsnMaximize   = True         ; Maximize plot in frame.
ResC@gsnLeftString=""
ResC@gsnRightString=""
ResC@gsnStringFontHeightF = 0.010
ResC@sfXArray = lon 
ResC@sfYArray = lat 
ResC@cnFillMode = "rasterfill"

ResC2=ResC
ResC3=ResC
ResC5=ResC

ResC2@cnFillOn = False
ResC2@cnLinesOn= True
ResC3@cnFillOn = True
ResC3@cnLinesOn= False

ResC@cnFillOn = True ; do color fill
ResC@cnLinesOn=False
ResC@lbLabelBarOn = False 
ResC@cnLineLabelsOn = False 

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

ResC@mpOutlineOn = True 
ResC@mpOutlineDrawOrder = "PostDraw"
ResC@mpGeophysicalLineThicknessF = 2
ResC@mpGeophysicalLineColor ="black"
ResC@mpDataSetName         = "Earth..4"     
ResC@mpFillOn = False 
ResC@pmTickMarkDisplayMode = True
ResC2@cnLevelSpacingF = 7
ResC2@cnInfoLabelOn = False  
ResC2@cnLineThicknessF = 2
ResC2@cnLineColor = "coral"
ResC2@cnLineLabelFontHeightF = 0.004
ResC2@cnLineLabelDensityF = 1.5
; ResC2@cnLabelMasking             = True        
ResC2@cnLineLabelBackgroundColor = "transparent"

ResC@cnLevelSelectionMode = "ManualLevels"
ResC@cnMinLevelValF = 5
ResC@cnMaxLevelValF = 150 
ResC@cnLevelSpacingF = .5


cmap_r              = read_colormap_file("MPL_Greys")
cmap_r_sub         = cmap_r(0:70,:)
ResC@cnFillPalette = cmap_r_sub

ResC3@cnLevelSelectionMode = "ExplicitLevels"
ResC3@cnLevels = (/0.5, 1, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 5, 6, 7, 8, 9, 10, 12, 15, 20/)
cmap2_r              = read_colormap_file("precip2_17lev")
cmap2_r(0,:)         = 0.0    ; Fully transparent
ResC3@cnFillPalette = cmap2_r

; ResC3@lbOrientation = "Vertical"
; ResC3@pmLabelBarWidthF = 0.02
; ResC3@pmLabelBarOrthogonalPosF = 0.005
; ResC3@lbLabelFontHeightF = 0.005

ResC3@lbOrientation = "Vertical"
; ResC3@pmLabelBarHeightF = 0.04
ResC3@pmLabelBarWidthF = 0.02
ResC3@pmLabelBarOrthogonalPosF = 0.005
ResC3@lbLabelFontHeightF = 0.005
ResC3@lbTitleOn = True 
ResC3@lbTitleString = "Rain [mm]"
ResC3@lbTitlePosition = "Bottom"
ResC3@lbTitleFontHeightF = 0.006
ResC3@lbTitleDirection = "Down"

ResC5@cnLinesOn = False 
ResC5@cnFillOn=True 
cmap5_r              = read_colormap_file("MPL_PuRd")
; cmap5_r(0,4)         = 0.2   
ResC5@cnFillPalette = cmap5_r(20:,:)
ResC5@pmLabelBarHeightF = 0.6
ResC5@lbLabelFontHeightF = 0.005
ResC5@cnLevelSelectionMode = "ExplicitLevels"
ResC5@cnLevels = (/1, 1.5, 2, 2.5, 3, 4, 5, 10, 20/)

ResC5@lbAutoManage = False 
ResC5@lbOrientation = "Horizontal"
ResC5@pmLabelBarHeightF = 0.03
ResC5@pmLabelBarOrthogonalPosF = -0.016
ResC5@lbLabelFontHeightF = 0.005
ResC5@lbTitleOn = True 
ResC5@lbTitleString = "Snow [mm eq.]"
ResC5@lbTitlePosition = "Right"
ResC5@lbTitleFontHeightF = 0.008
ResC5@lbTitleDirection = "Across"
ResC5@lbLabelPosition  = "Center"             ; label position
ResC5@lbLabelAlignment = "BoxCenters"         ; label orientation


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
   wks = gsn_open_wks("png","precip_clouds_"+date_string(time_i))

   plot = gsn_csm_contour_map(wks,clcm(time_i,:),ResC)
   over = gsn_csm_contour(wks,mslp(time_i,:),ResC2)
   over_rain=gsn_csm_contour(wks, rain(time_i,:), ResC3)
   over_snow=gsn_csm_contour(wks, change_snow(time_i,:), ResC5)


   text=gsn_create_text(wks, run_string, txres)
   run_annotation=gsn_add_annotation(plot, text, amres)

   text2=gsn_create_text(wks, plot_description, txres)
   description=gsn_add_annotation(plot, text2, amres2)

   overlay(plot, over_rain)
   overlay(plot, over_snow)
   overlay(plot, over)
   draw(plot)
   frame(wks)

end do
end
