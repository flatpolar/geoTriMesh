import os
import sys
import subprocess
import gdal, ogr
import numpy as np
import json
import argparse
import time




def read_dem(filepath):

    print(filepath)

    #"""
    dem_dataset = gdal.Open(filepath)
    dem_tmp_cols = dem_dataset.RasterXSize
    dem_tmp_rows = dem_dataset.RasterYSize
    dem_geotransform = dem_dataset.GetGeoTransform()
    dem_xres = dem_geotransform[1]
    dem_yres = abs(dem_geotransform[5])
    dem_xmin = dem_geotransform[0]
    dem_ymax = dem_geotransform[3]
    dem_xmax = dem_xmin + dem_tmp_cols * dem_xres
    dem_ymin = dem_ymax - dem_tmp_rows * dem_yres
    dem_band = dem_dataset.GetRasterBand(1)
    dem_tmp_array = dem_band.ReadAsArray(0, 0, dem_tmp_cols, dem_tmp_rows).astype(np.float32)
    dem_nodata = dem_band.GetNoDataValue()
    dem_xcent = (dem_xmin + dem_xmax) / 2.0
    dem_ycent = (dem_ymin + dem_ymax) / 2.0
    dem_ydist = dem_ymax - dem_ymin
    dem_xdist = dem_xmax - dem_xmin

    #dem_tmp_array = np.copy(np.flipud(dem_tmp_array))
    dem_tmp_nodata_range_external = [-9999, 9999]

    print(dem_tmp_rows, dem_tmp_cols)

    if True:
        dem_tmp_nodata = -9999

        dem_tmp_array[dem_tmp_array < dem_tmp_nodata_range_external[0]] = dem_tmp_nodata
        dem_tmp_array[dem_tmp_array > dem_tmp_nodata_range_external[1]] = dem_tmp_nodata

        dem_tmp_array[dem_tmp_array<-500] = -9999

        dem_intermed_array = dem_tmp_array


        try:
            #print(dem_intermed_array.shape)

            dem_tmp_array_valmin = np.nanmin(dem_intermed_array[dem_intermed_array != dem_tmp_nodata])
            dem_tmp_array_valmax = np.nanmax(dem_intermed_array[dem_intermed_array != dem_tmp_nodata])
        except:
            with open(os.path.join(scad_dirpath, scad_filename_base + '.scad.empty'), 'w') as scad_file:
                scad_file.write('')
        
            sys.exit()




        dem_array = dem_intermed_array



        dem_rows, dem_cols = dem_array.shape


    return dem_array, dem_cols, dem_rows, dem_xmin, dem_ymax, dem_xres, dem_yres, dem_xdist, dem_ydist



def generate_terrain(clippoly_filepath, dem_dirpath, dem_prefix, dem_tilex, dem_tiley, zmean_total):


    dem_filepath = os.path.join(dem_dirpath, '_'.join([dem_prefix, dem_tiley, dem_tilex]) + ".tif")

    print("dem_filepath", dem_filepath, clippoly_filepath, dem_dirpath, dem_prefix, dem_tilex, dem_tiley)

    polygon_extrude_height = 10000.0
    polyhedron_extrude_height = 100.0


    clippoly_driver = ogr.GetDriverByName("ESRI Shapefile")
    clippoly_datasource = clippoly_driver.Open(clippoly_filepath, 0)
    clippoly_layer = clippoly_datasource.GetLayer()
    clippoly_layer_extent = clippoly_layer.GetExtent()

    clippoly_layer_extent_xmin = clippoly_layer_extent[0]
    clippoly_layer_extent_xmax = clippoly_layer_extent[1]
    clippoly_layer_extent_ymin = clippoly_layer_extent[2]
    clippoly_layer_extent_ymax = clippoly_layer_extent[3]

    clippoly_layer_extent_xcent = (clippoly_layer_extent_xmax + clippoly_layer_extent_xmin) / 2.0
    clippoly_layer_extent_ycent = (clippoly_layer_extent_ymax + clippoly_layer_extent_ymin) / 2.0





    c = []

    dem_array, dem_cols, dem_rows, dem_xmin, dem_ymax, dem_xres, dem_yres, dem_xdist, dem_ydist = read_dem(dem_filepath)

    print("nanmin", np.nanmin(dem_array))
    dem_array = np.copy(dem_array-zmean_total)
    print("nanmin", np.nanmin(dem_array))


    if True:


        if True:


            polyhedron_points = []
            polyhedron_points_floor = []
            polyhedron_points_ceil = []
            polyhedron_faces = []
            polyhedron_faces_array = np.zeros((dem_rows,dem_cols,16,3), dtype=np.int32)
            polyhedron_faces_clean_array = np.zeros((dem_rows,dem_cols,16,3), dtype=np.int32)
            polyhedron_points_floor_array = np.zeros((dem_rows*dem_cols,3), dtype=np.float32)
            #polyhedron_points_ceil_array = np.zeros((dem_rows*dem_cols,3), dtype=np.float32)

            z_scale = 1.0
            cnt = 0

            dem_x_min = None
            dem_x_max = None
            dem_y_min = None
            dem_y_max = None


            #for i in range(dem_rows,-1,-1):
            for i in range(0,dem_rows):


                for j in range(0,dem_cols):



                    #i0_coord = (dem_ymax - ((dem_yres*-1) * i) - (0.5 * (dem_yres*-1))) - dem_ydist
                    #j0_coord = dem_xmin + (dem_xres * j) + (0.5 * dem_xres)


                    i0_coord = dem_ymax - (dem_yres * i) #- dem_ydist #- (0.5 * (dem_yres*-1)))
                    j0_coord = dem_xmin + (dem_xres * j) #+ (0.5 * dem_xres)



                    #print(i,j,i0_coord,j0_coord)

                    z_a = (dem_array[i][j] * z_scale) #- zmean_total


                    dem_x = j0_coord 
                    dem_y = i0_coord

                    polyhedron_points_floor_array[(i*dem_cols)+j][:] = np.array([dem_x - clippoly_layer_extent_xcent, dem_y  - clippoly_layer_extent_ycent, z_a])
                    #polyhedron_points_floor_array[cnt][:] = np.array([j0_coord - clippoly_layer_extent_xcent, i0_coord - clippoly_layer_extent_ycent, z_a])



                    if not dem_x_min or dem_x < dem_x_min:
                        dem_x_min = dem_x
                    if not dem_x_max or dem_x > dem_x_max:
                        dem_x_max = dem_x

                    if not dem_y_min or dem_y < dem_y_min:
                        dem_y_min = dem_y
                    if not dem_y_max or dem_y > dem_y_max:
                        dem_y_max = dem_y


                    #print(dem_rows*dem_cols, cnt, (i*dem_rows)+j, dem_rows, dem_cols, i, j, z_a)


                    if i<dem_rows-1 and j < dem_cols-1:

                        z_b = (dem_array[i+1][j] * z_scale) #- zmean_total
                        z_c = (dem_array[i][j+1] * z_scale) #- zmean_total
                        z_d = (dem_array[i+1][j+1] * z_scale) #- zmean_total

                        point_a_ceil = (i*dem_cols)+j
                        point_b_ceil = ((i+1)*dem_cols)+j
                        point_c_ceil = (i*dem_cols)+j+1
                        point_d_ceil = ((i+1)*dem_cols)+j+1

                        point_a_floor = (dem_rows*dem_cols) + (i*dem_cols)+j
                        point_b_floor = (dem_rows*dem_cols) + ((i+1)*dem_cols)+j
                        point_c_floor = (dem_rows*dem_cols) + (i*dem_cols)+j+1
                        point_d_floor = (dem_rows*dem_cols) + ((i+1)*dem_cols)+j+1

                        
                        
                        if z_a > -5000 and z_b > -5000 and z_c > -5000:


                            polyhedron_faces_array[i][j][0][:] = np.array([point_c_ceil, point_b_ceil, point_a_ceil])     ## ceiling 
                            polyhedron_faces_array[i][j][1][:] = np.array([point_b_floor, point_a_floor, point_a_ceil])   ## left sidev 
                            polyhedron_faces_array[i][j][2][:] = np.array([point_b_ceil, point_b_floor, point_a_ceil])
                            polyhedron_faces_array[i][j][3][:] = np.array([point_c_floor, point_b_floor, point_b_ceil])   ## right side (diagonal)
                            polyhedron_faces_array[i][j][4][:] = np.array([point_c_ceil, point_c_floor, point_b_ceil])
                            polyhedron_faces_array[i][j][5][:] = np.array([point_a_floor, point_c_floor, point_c_ceil])   ## top side
                            polyhedron_faces_array[i][j][6][:] = np.array([point_a_ceil, point_a_floor, point_c_ceil])
                            polyhedron_faces_array[i][j][7][:] = np.array([point_a_floor, point_b_floor, point_c_floor])  ## floor




                        if z_b > -5000 and z_d > -5000 and z_c > -5000:

                            polyhedron_faces_array[i][j][8][:] = np.array([point_c_ceil, point_d_ceil, point_b_ceil])     ## ceiling
                            polyhedron_faces_array[i][j][9][:] = np.array([point_d_ceil, point_d_floor, point_b_floor])   ## bottom side
                            polyhedron_faces_array[i][j][10][:] = np.array([point_d_ceil, point_b_floor, point_b_ceil])
                            polyhedron_faces_array[i][j][11][:] = np.array([point_c_ceil, point_c_floor, point_d_floor])   ## right side
                            polyhedron_faces_array[i][j][12][:] = np.array([point_c_ceil, point_d_floor, point_d_ceil])
                            polyhedron_faces_array[i][j][13][:] = np.array([point_b_ceil, point_b_floor, point_c_floor])   ## left side (diagonal)
                            polyhedron_faces_array[i][j][14][:] = np.array([point_c_ceil, point_b_ceil, point_c_floor])
                            polyhedron_faces_array[i][j][15][:] = np.array([point_b_floor, point_d_floor, point_c_floor])  ## floor


                    cnt += 1



    print(polyhedron_points_floor_array[-1])


    polyhedron_faces_clean = []


    for i in range(0,dem_rows):
        for j in range(0,dem_cols):


            for polyhedron_face_id in range(0, 16):

                polyhedron_face = polyhedron_faces_array[i][j][polyhedron_face_id][:].tolist()
                polyhedron_face_cnt = 0


                if not (polyhedron_face[0] == 0 and polyhedron_face[1] == 0 and polyhedron_face[2] == 0):

                    i_bottom = i - 1 if i > 0 else 0
                    i_top = i + 1 if i < dem_rows-1 else dem_rows-1
                    j_left = j - 1 if i > 0 else 0
                    j_right = j + 1 if j < dem_cols-1 else dem_cols


                    for i_neighbour in range(i_bottom, i_top+1): 
                        for j_neighbour in range(j_left, j_right+1): 

                            array1 = np.array([polyhedron_face[0], polyhedron_face[1], polyhedron_face[2]])
                            array2 = np.array([polyhedron_face[0], polyhedron_face[2], polyhedron_face[1]])
                            array3 = np.array([polyhedron_face[1], polyhedron_face[0], polyhedron_face[2]])
                            array4 = np.array([polyhedron_face[1], polyhedron_face[2], polyhedron_face[0]])
                            array5 = np.array([polyhedron_face[2], polyhedron_face[1], polyhedron_face[0]])
                            array6 = np.array([polyhedron_face[2], polyhedron_face[0], polyhedron_face[1]])

                            loc1 = np.where(np.all(polyhedron_faces_array[i_neighbour][j_neighbour][:]==array1, axis=1))
                            loc2 = np.where(np.all(polyhedron_faces_array[i_neighbour][j_neighbour][:]==array2, axis=1))
                            loc3 = np.where(np.all(polyhedron_faces_array[i_neighbour][j_neighbour][:]==array3, axis=1))
                            loc4 = np.where(np.all(polyhedron_faces_array[i_neighbour][j_neighbour][:]==array4, axis=1))
                            loc5 = np.where(np.all(polyhedron_faces_array[i_neighbour][j_neighbour][:]==array5, axis=1))
                            loc6 = np.where(np.all(polyhedron_faces_array[i_neighbour][j_neighbour][:]==array6, axis=1))

                            polyhedron_face_neighbour_cnt = len(loc1[0]) + len(loc2[0]) + len(loc3[0]) + len(loc4[0]) + len(loc5[0]) + len(loc6[0])
                            polyhedron_face_cnt += polyhedron_face_neighbour_cnt






                    if polyhedron_face_cnt == 1:

                        polyhedron_faces_clean.append(polyhedron_face)

                    else:
                        pass





    polyhedron_points = []

    for l in range(1,-1,-1):
        for polyhedron_point_id in range(0, polyhedron_points_floor_array.shape[0]):

            polyhedron_point = [polyhedron_points_floor_array[polyhedron_point_id][0],
              polyhedron_points_floor_array[polyhedron_point_id][1], 
              polyhedron_points_floor_array[polyhedron_point_id][2]-(l*10.0)]
 
            #print(polyhedron_point)
            polyhedron_points.append(polyhedron_point)

        



    print('dem_extent:', dem_x_min, dem_y_min, dem_x_max, dem_y_max)
    print(clippoly_layer_extent_xcent, clippoly_layer_extent_ycent)




    print('points', len(polyhedron_points))
    print('faces', polyhedron_faces_array.shape[0])
    print('faces_clean', len(polyhedron_faces_clean))

    c.append('module dem() {')
    c.append('  polyhedron(points={}, faces={});'.format(polyhedron_points, polyhedron_faces_clean))
    c.append('}')

    #c.append('dem();')





    clippoly_layer.ResetReading()
    for feat_id, feat in enumerate(clippoly_layer):
        geom = feat.GetGeometryRef()
        geom_name = str(geom.GetGeometryName())
        geom_subgeomcount = geom.GetGeometryCount()


        if geom_name.lower() == 'multipolygon':

            ## iterate over sub polygons
            for sub_id in range(0, geom.GetGeometryCount()):

                polygon_points = []
                polygon_paths = []
                point_cnt = 0


                geom_sub = geom.GetGeometryRef(sub_id)
                geom_sub_subgeomcount = geom_sub.GetGeometryCount()



                for bound_id in range(0, geom_sub_subgeomcount):
                    polygon_path = []

                    geom_sub_bound = geom_sub.GetGeometryRef(bound_id)


                    geom_sub_bound_json = json.loads(geom_sub_bound.ExportToJson())
                    polygon_path = [] #geom_sub_bound_json['coordinates']

                    for point_id in range(0, geom_sub_bound.GetPointCount()-1):
                        geom_sub_bound_point_x, geom_sub_bound_point_y, dummy = geom_sub_bound.GetPoint(point_id)

                    
                        polygon_path.append(point_cnt)
                        polygon_points.append([geom_sub_bound_point_x - clippoly_layer_extent_xcent, geom_sub_bound_point_y - clippoly_layer_extent_ycent])
                        #polygon_points.append([0, 0])
                        point_cnt +=1


                    polygon_paths.append(polygon_path)


                c.append('intersection() {')
                c.append('translate([0,0,-5000]) linear_extrude(height={}) polygon({},{});'.format(polygon_extrude_height, polygon_points, polygon_paths))
                c.append('dem();')
                c.append('}')




        elif geom_name.lower() == 'polygon':

            polygon_points = []
            polygon_paths = []
            point_cnt = 0


            for bound_id in range(0, geom_subgeomcount):
                geom_bound = geom.GetGeometryRef(bound_id)

                geom_bound_json = json.loads(geom_bound.ExportToJson())
                polygon_path = [] #geom_bound_json['coordinates']



                for point_id in range(0, geom_bound.GetPointCount()):
                    geom_bound_point_x, geom_bound_point_y, dummy = geom_bound.GetPoint(point_id)
                
                    polygon_path.append(point_cnt)
                    polygon_points.append([geom_bound_point_x - clippoly_layer_extent_xcent, geom_bound_point_y - clippoly_layer_extent_ycent])
                    #polygon_points.append([0, 0])
                    #print(geom_bound_point_x - clippoly_layer_extent_xcent, geom_bound_point_y - clippoly_layer_extent_ycent)
                    #print(clippoly_layer_extent_xcent, clippoly_layer_extent_ycent)
                    point_cnt +=1


                polygon_paths.append(polygon_path)


            c.append('intersection() {')
            c.append('translate([0,0,-5000]) linear_extrude(height={}) polygon({},{});'.format(polygon_extrude_height, polygon_points, polygon_paths))
            c.append('dem();')
            c.append('}')



    from operator import itemgetter 
  

    return c 
















scad_filename_base = 'test'
proc_target_os = 'win'

openscad_bin_filepath = 'openscad'
scad_dirpath = os.path.join(os.sep, 'mnt', 'c', 'Users', 'mic', 'dev')
proc_dirpath = os.path.join(os.sep, 'mnt', 'c', 'Users', 'mic', 'dev')


dem_filepath = os.path.join(os.sep, 'mnt', 'e', 'zh', 'gis_zh__dom_dtm__lidar', 'dtm_mosaic_tiled_offset_500x500', 'dtm_mosaic_tiled_offset_500x500_34_33.tif')
clippoly_filepath = os.path.join(os.sep, 'mnt', 'e', 'zh', 'wambachers_osm__boundaries__adm', 'data', 'district_zurich_al6_al6_2056.shp')



parser = argparse.ArgumentParser()
parser.add_argument('--dem_path', action='store', type=str, required=True)
parser.add_argument('--dem_prefix', action='store', type=str, required=True)
parser.add_argument('--dem_tilex', action='store', type=str, required=True)
parser.add_argument('--dem_tiley', action='store', type=str, required=True)
parser.add_argument('--zmin', action='store', type=str, required=False)
parser.add_argument('--zmax', action='store', type=str, required=False)
parser.add_argument('--clippoly', action='store', type=str, required=True)
parser.add_argument('--outdir', action='store', type=str, required=True)

args = parser.parse_args()

dem_dirpath = args.dem_path
dem_prefix = args.dem_prefix
dem_tilex = args.dem_tilex
dem_tiley = args.dem_tiley
clippoly_filepath = args.clippoly
proc_dirpath = args.outdir
#sys.exit()
#dem_dirpath, dem_filename = os.path.split(dem_filepath)
#dem_filename_base = dem_filename.split('.')[0]
scad_dirpath = args.outdir

scad_filename_base = "_".join([dem_prefix, dem_tiley, dem_tilex])
try:
    zmin_total = float(args.zmin)
    zmax_total = float(args.zmax)
    zmean_total = zmin_total + ((zmax_total - zmin_total) / 2.0)
except:
    zmean_total = 0

command_lines = []


#if not (os.path.isfile(os.path.join(scad_dirpath, scad_filename_base + '.bat')) or os.path.isfile(os.path.join(scad_dirpath, scad_filename_base + '.sh'))):
if True:

    terrain_command_lines = generate_terrain(clippoly_filepath, dem_dirpath, dem_prefix, dem_tilex, dem_tiley, zmean_total)
    command_lines += terrain_command_lines



    with open(os.path.join(scad_dirpath, scad_filename_base + '.scad'), 'w') as scad_file:
        for command_line in command_lines:
            scad_file.write(command_line + '\n')



    if not proc_target_os == 'win':

        subprocess_bin = openscad_bin_filepath
        subprocess_commands = [subprocess_bin, '-o', os.path.join(proc_dirpath, scad_filename_base + '.stl'), os.path.join(scad_dirpath, scad_filename_base + '.scad')]
        output = subprocess.check_output(subprocess_commands, shell=False)

    else:

        openscad_win_bin_filepath = '\\'.join(['C:', '"Program Files"', 'OpenSCAD', 'openscad.com'])
        openscad_linux_bin_filepath = os.path.join(os.sep, 'home', 'mic', 'prog', 'OpenSCAD-2019.05-x86_64', 'squashfs-root', 'usr', 'bin', 'openscad')

        scad_win_dirpath = '\\'.join(['C:', 'Users', 'mic', 'dev'])
        proc_win_dirpath = '\\'.join(['C:', 'Users', 'mic', 'dev'])

        subprocess_args = ['-o', scad_filename_base + '.stl', scad_filename_base + '.scad']
        subprocess_win_command = [openscad_win_bin_filepath] + subprocess_args
        subprocess_linux_command = [openscad_linux_bin_filepath] + subprocess_args

        with open(os.path.join(scad_dirpath, scad_filename_base + '.bat'), 'w') as batch_file:
            batch_file.write(' '.join(subprocess_win_command))

        with open(os.path.join(scad_dirpath, scad_filename_base + '.sh'), 'w') as shell_file:
            shell_file.write(' '.join(subprocess_linux_command))


