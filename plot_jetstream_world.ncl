load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/cd_string.ncl"

begin
; Open model level output file

wkstype="png"
wkstype@wkWidth = 1100
wkstype@wkHeight = 1100

fils = systemfunc ("ls /scratch/local1/m300382/icon_globe/ICON_*_3h.nc") ; file paths
f_pres    = addfiles (fils, "r")  
ListSetType (f_pres, "cat")

lev1=300

plot_description="Winds (intensity in km/h) and geopotential (dam) at "+lev1+" hPa"

RAD2DEG = get_r2d("float")

lev1=lev1*100
geopt=f_pres[:]->z(:,{lev1},:)
geopt=geopt/100.
u=f_pres[:]->u(:,{lev1},:)
v=f_pres[:]->v(:,{lev1},:)
speed=sqrt(u^2+v^2)*3.6

copy_VarCoords(u, speed)

lon = f_pres[:]->clon * RAD2DEG 
lat = f_pres[:]->clat * RAD2DEG
time= f_pres[:]->time

date_string=time/60
run_time=str_sub_str(time@units,"minutes since ","")
run_string="Run: "+run_time

delete([/fils, f_pres, u, v/])

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
ResC@cnFillMode = "RasterFill"
ResC@cnMissingValFillColor=0
ResC@cnLinesOn=False

ResC@tmXBBorderOn      = False
ResC@tmXBOn            = False
ResC@tmXTBorderOn      = False
ResC@tmXTOn            = False
ResC@tmYLBorderOn      = False
ResC@tmYLOn            = False
ResC@tmYRBorderOn      = False
ResC@tmYROn            = False

ResC@mpProjection = "Robinson"

ResC@mpGeophysicalLineThicknessF = 1
ResC@mpGeophysicalLineColor ="black"
ResC@mpDataSetName         = "Earth..4"     
ResC@mpFillOn = True
ResC@mpOutlineOn = True 
ResC@pmTickMarkDisplayMode = True

ResC2@cnLevelSelectionMode = "ManualLevels"
ResC2@cnMinLevelValF = round(min(geopt),0)
ResC2@cnMaxLevelValF = round(max(geopt),0)
ResC2@cnLevelSpacingF = 15
ResC2@cnInfoLabelOn = False  
ResC2@cnLineThicknessF = 3
ResC2@cnLineColor = "gray70"
ResC2@cnLineLabelFontHeightF = 0.004
ResC2@cnLineLabelDensityF = 1.5
; ResC2@cnLabelMasking             = True        
ResC2@cnLineLabelBackgroundColor = "transparent"
 ;ResC2@cnLowLabelsOn = True
 ;ResC2@cnLowLabelBackgroundColor = -1
; ResC2@cnLowLabelString = "L"
 ;ResC2@cnHighLabelsOn = True
 ;ResC2@cnHighLabelBackgroundColor = -1
 ;ResC2@cnHighLabelString = "H"

ResC@lbLabelFontHeightF = 0.01
ResC@lbBoxEndCapStyle = "TriangleBothEnds"

cmap_r=read_colormap_file("wind_17lev")
cmap_r(0,:)=0.0
ResC@cnFillPalette= cmap_r

; ResC@cnFillPalette = "wind_17lev"
ResC@cnLevelSelectionMode = "ManualLevels"
ResC@cnMinLevelValF = 50
ResC@cnMaxLevelValF = 250 
ResC@cnLevelSpacingF = 10
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
   wks = gsn_open_wks(wkstype,"world/winds_jet_"+date_string(time_i))

   plot = gsn_csm_contour_map(wks,speed(time_i,:),ResC)
   over = gsn_csm_contour(wks,geopt(time_i,:),ResC2)

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
