load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/time_axis_labels.ncl"

; These variables are provided outside when the script is called 
if .not.isvar("lat_point") then
	lat_point=51.800556
end if
if .not.isvar("lon_point") then
	lon_point=10.6172222
end if
if .not.isvar("city") then
	city="Brocken"
end if

;***********************************************
begin
;***********************************************

fils = systemfunc ("ls "+file_in) ; file paths
f_in    = addfiles (fils, "r")  
;ListSetType (f_in, "cat")

orography=addfile("~/icon_globe/ICON_iko_invar_package_world_grid.nc", "r")
height=orography->h(0,:)

RAD2DEG = get_r2d("float")

lon = f_in[:]->clon * RAD2DEG 
lat = f_in[:]->clat * RAD2DEG
time= f_in[:]->time 
lev = f_in[:]->plev

run_time=str_sub_str(time@units,"minutes since ","")
run_string="Run: "+run_time

; Find closest point to lat/lon value 
diff_lon=abs(lon-lon_point)
diff_lat=abs(lat-lat_point)
diff_squared=sqrt(diff_lon^2+diff_lat^2)
ind_point=minind(diff_squared)
;

dims_3D=(/dimsizes(time),dimsizes(lev)/)
dims_2D=(/dimsizes(time)/)
;
; Add variables but first check whether they exist or not, otherwise create
; array with missing value in order not to screw up the whole script
;
if isfilevar(f_in[0], "u") then
	u=f_in[:]->u(:,:,ind_point)
else 
	u=new(dims_3D, float)
end if
;
if isfilevar(f_in[0], "v") then
	v=f_in[:]->v(:,:,ind_point)
else 
	v=new(dims_3D, float)
end if
;
if isfilevar(f_in[0], "t") then
	temp=f_in[:]->t(:,:,ind_point)
else 
	temp=new(dims_3D, float)
end if
temp=temp-273.15
;
if isfilevar(f_in[0], "r") then
	rh=f_in[:]->r(:,:,ind_point)
else 
	rh=new(dims_3D, float)
end if

; Convert pressure levels to hPa
u&plev=u&plev/100.
v&plev=v&plev/100.
temp&plev=temp&plev/100.
rh&plev=rh&plev/100.

; Subset 2-D variables and check whether they exist or not
if isfilevar(f_in[0], "prmsl") then
        mslp_point=f_in[:]->prmsl(:,ind_point)
else
        mslp_point=new(dims_2D, float)
end if
mslp_point=mslp_point/100.
;
if isfilevar(f_in[0], "2t") then
        t2m_point=f_in[:]->2t(:,0,ind_point)
else
        t2m_point=new(dims_2D, float)
end if
t2m_point=t2m_point-273.15
;
if isfilevar(f_in[0], "2d") then
        dewp_point=f_in[:]->2d(:,0,ind_point)
else
        dewp_point=new(dims_2D, float)
end if
dewp_point=dewp_point-273.15
;
if isfilevar(f_in[0], "10fg3") then
        gust_point=f_in[:]->10fg3(:,0,ind_point)
else
        gust_point=new(dims_2D, float)
end if
gust_point=gust_point*3.6

height_point=height(ind_point)
;;;;;;;;;;;;;;;;;;;;;;;;;
; Precipitation variables 
;;;;;;;;;;;;;;;;;;;;;;;;;
if isfilevar(f_in[0], "SNOW_CON") then
        snow_con=f_in[:]->SNOW_CON(:,ind_point)
else
        snow_con=new(dims_2D, float)
end if
;
if isfilevar(f_in[0], "SNOW_GSP") then
        snow_gsp=f_in[:]->SNOW_GSP(:,ind_point)
else
        snow_gsp=new(dims_2D, float)
end if
;
if isfilevar(f_in[0], "RAIN_CON") then
        rain_con=f_in[:]->RAIN_CON(:,ind_point)
else
        rain_con=new(dims_2D, float)
end if
;
if isfilevar(f_in[0], "RAIN_GSP") then
        rain_gsp=f_in[:]->RAIN_GSP(:,ind_point)
else
        rain_gsp=new(dims_2D, float)
end if

snow_acc=snow_con + snow_gsp
copy_VarMeta(snow_con, snow_acc)
rain_acc=rain_con + rain_gsp
copy_VarMeta(rain_con, rain_acc)
rain_point=rain_acc
rain_point=rain_point*0.
snow_point=snow_acc
snow_point=snow_point*0.
do i=1,dimsizes(time)-1
  rain_point(i)=rain_acc(i)-rain_acc(i-1) 
end do 
do i=1,dimsizes(time)-1
  snow_point(i)=snow_acc(i)-snow_acc(i-1) 
end do 

;rain_point=mask(rain_point, rain_point.le.0.01, 0)
;snow_point=mask(snow_point, snow_point.le.0.01, 0)
rain_point=rain_point/3.
snow_point=snow_point/3.

; Reorder arrays
temp_point=temp(plev|:,time|:)
u_point=u(plev|:,time|:)
v_point=v(plev|:,time|:)
rh_point=rh(plev|:,time|:)

;-----------------------------------------------------------------------
res2D = True                            ; Set basic resources 
res2D@gsnDraw              = False      ; Don't draw individual plot.
res2D@gsnFrame             = False      ; Don't advance frame.
res2D@vpWidthF             = 0.70       ; width
res2D@vpHeightF            = 0.35       ; height

; res2D@tmYROn = False 
res2D@tmXBOn = False 
res2D@tiXAxisString = ""

res2D@gsnLeftString =  "ICON"
res2D@gsnRightString = "Copyright DWD"
res2D@gsnLeftStringFontHeightF = 0.01
res2D@gsnRightStringFontHeightF = 0.01
res2D@trYReverse = True
res2D@tiYAxisString = "pressure [hPa]"

tt_res = res2D
tt_res@tiMainFontHeightF =0.02
tt_res@cnFillPalette ="NCV_jet" 
tt_res@cnFillOn                 = True             ; turns on color fill
tt_res@cnLevelSelectionMode     = "ManualLevels"   ; set levels manually
tt_res@cnMinLevelValF           = -50.
tt_res@cnMaxLevelValF           = 25.
tt_res@cnLevelSpacingF          = 2.5
; tt_res@cnLinesOn                = False
tt_res@cnLineThicknessF = 0.005
tt_res@gsnContourZeroLineThicknessF = 3
tt_res@cnLineLabelsOn           = False
tt_res@cnInfoLabelOn            = False
; tt_res@pmLabelBarDisplayMode    = "Always"         ; Add a label bar

tt_res@lbOrientation = "Vertical"
tt_res@pmLabelBarWidthF = 0.08
tt_res@pmLabelBarHeightF = 0.35
tt_res@pmLabelBarOrthogonalPosF = -0.01
; tt_res@lbLabelPosition  = "Center"             ; label position
; tt_res@lbLabelAlignment = "BoxCenters"         ; label orientation
tt_res@lbLabelFontHeightF = 0.009
tt_res@lbTitleOn = True 
tt_res@lbTitleString = "[C]"
tt_res@lbTitlePosition = "Bottom"
tt_res@lbTitleFontHeightF = 0.008
tt_res@lbTitleDirection = "Across"
tt_res@lbOrientation = "Vertical"

uv_res = res2D
uv_res@vcRefAnnoOn      = False         ; turns off the ref vector
uv_res@vcRefLengthF     = 0.015         ; set length of ref vector
uv_res@vcMapDirection = False 
uv_res@vcMinDistanceF    = 0.015
uv_res@vcGlyphStyle     = "WindBarb"    ; turn on wind barbs
uv_res@vcWindBarbLineThicknessF = 4
uv_res@vcWindBarbColor = "grey60"

rh_res=res2D 
rh_res@cnFillOn=False 
rh_res@cnLinesOn = True 
rh_res@cnLevelSelectionMode = "ExplicitLevels"
rh_res@cnLevels = (/50, 70, 100/)
rh_res@cnLineThicknessF = 3
rh_res@cnLineColor = "white"
rh_res@cnInfoLabelOn = False 
rh_res@cnLineLabelFontHeightF = 0.006

amres=True 
amres@amParallelPosF   = -0.25    ; This is the right edge of the plot.
amres@amOrthogonalPosF = -0.5    ; This is the bottom edge of the plot.
amres@amJust = "BottomLeft"

txres                       = True
txres@txPerimOn             = True
txres@txBackgroundFillColor = "White"
txres@txFontHeightF         = 0.01

;-----------------------------------------------------------------------

res1D = True                            ; Set basic resources both will use
res1D@vpWidthF          = 0.70          ; The Width of the plot box
res1D@vpHeightF         = 0.11          ; The height of the plot box
res1D@tmXTOn            = False         ; turn off the top tick marks
res1D@xyLineThicknessF = 4             ; increase line thickness
res1D@gsnDraw           = False         ; Don't draw individual plot.
res1D@gsnFrame          = False         ; Don't advance frame.
res1D@trXMinF = min(time)
res1D@trXMaxF = max(time)
res1D@tmYLLabelFontHeightF = 0.005

res_xy = res1D
res_xy@trYMinF = 0.
res_xy@xyLineColors     = (/"blue","purple"/)         ; set line color
res_xy@xyDashPattern = 0
res_xy@tiYAxisString   = "Rain/snow"        ; set y-axis string
res_xy@tmXBLabelsOn = False
res_xy@tmYLLabelsOn = False
res_xy@tmYRLabelsOn = True
res_xy@tmYLLabelDeltaF = 1.5
res_xy@tmYMajorGrid = True 
res_xy@tmYMajorGridThicknessF = 0.4

res_xy@pmLegendDisplayMode    = "Always"
res_xy@pmLegendSide           = "Bottom"               ; Change location of 
res_xy@pmLegendParallelPosF   = 0.5                 ; move units right
res_xy@pmLegendOrthogonalPosF = -0.95                ; move units down
res_xy@pmLegendWidthF         = 0.07                ; Change width and
res_xy@pmLegendHeightF        = 0.02                ; height of legend.
res_xy@lgLabelFontHeightF     = .007                 ; change font height
res_xy@lgPerimFill            = "SolidFill"      ; Fill legend box w/white
res_xy@lgPerimFillColor       = "white"          ; so it masks XY curves
res_xy@lgOrientation          = "vertical"
res_xy@lgPerimOn              = True               ; turn off box
res_xy@xyExplicitLegendLabels = (/"Rain [mm/h]","Snow [mm eq/h]"/)

t2_res = res1D
t2_res@vpHeightF         = 0.13          ; The height of the plot box
t2_res@xyLineColors      = (/"black","blue"/)        ; set line color
t2_res@tiYAxisString   = "2m T/T~B~D~N~ [C]"        ; set y-axis string
t2_res@tiYAxisSide  = "Right"
t2_res@tmXBLabelFontHeightF = 0.0005
t2_res@tmXBLabelAngleF = 90
t2_res@tmXBLabelDeltaF = 2.
t2_res@tmYMajorGrid = True 
t2_res@tmYMajorGridThicknessF = 0.4

slp_res = res1D
slp_res@tmYLLabelDeltaF = 2.5

wind_res= res1D
wind_res@xyLineColor = "red"
wind_res@tiYAxisString=""
wind_res@tmYRLabelFontColor = "red"
wind_res@tmYRMajorLineColor = "red"
wind_res@tmYRMinorLineColor = "red"
wind_res@tmYMajorGrid = True 
wind_res@tmYMajorGridThicknessF = 0.4
wind_res@tmYMajorGridLineColor = "red"

slp_res@xyLineColor      = "black"        ; set line color
slp_res@tiYAxisString   = "MSLP/wind gust [km/h]"        ; set y-axis string
slp_res@tiYAxisSide  = "Right"
slp_res@tiYAxisOffsetXF = 0.05

;-----------------------------------------------------------------------

wks = gsn_open_wks("png","meteogram_"+city)    ; open a workstation

tt_res@tiMainString= "Meteogram for "+city+" ("+height_point+") m | "+run_string
ttfill    = gsn_csm_contour(wks,temp_point({1000:300},:),tt_res)
rhcont    = gsn_csm_contour(wks, rh_point, rh_res)

windlayer = gsn_csm_vector(wks,u_point({1000:300},:),v_point({1000:300},:),uv_res)
overlay(ttfill,windlayer)
overlay(ttfill,rhcont)

plot_description="Temperature, winds and cloud cover [%]"

text=gsn_create_text(wks, plot_description, txres)
description=gsn_add_annotation(windlayer, text, amres)

; Set special resources for the time axis
resTick                = True
resTick@ttmFormat      = "%d %c %H"
resTick@ttmMajorStride = 4
; Set resources necessary to customize Y axis labels
time_axis_labels( time,  t2_res, resTick )

rain_snow_plot  = gsn_csm_xy(wks,time,(/rain_point, snow_point/),res_xy)
mslp_wind_plot  = gsn_csm_xy2(wks, time, mslp_point, gust_point, slp_res, wind_res)

;obtain average of the plot 

t2_plot         = gsn_csm_xy(wks,time,(/t2m_point,dewp_point/),t2_res)

res1                     = True
res2                     = True
res1@gsnMaximize         = True
res2@gsnAttachPlotsXAxis = True

amid = gsn_attach_plots(ttfill,(/rain_snow_plot, mslp_wind_plot, t2_plot/),res1,res2)

draw(ttfill)
frame(wks)                            ; now frame the plot   

end
