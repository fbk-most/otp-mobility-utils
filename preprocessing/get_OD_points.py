#!/usr/bin/env python3
"""
Complete preprocessing pipeline for OD data.
Executes the steps described in the README in sequence.
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from utils import get_dataframe, put_dataframe, log_dataframe
from constants import CRS_LATLONG, CRS_PROJECTED, P2V
from params import local_raw, local_input, verbose
from params import file_centroids, file_shape, file_av, file_flows


def read_and_prepare_centroids(file_centroids, file_shape, file_av, local):
    # Assign av to OD shapes
    if not local:
        NotImplementedError("Non-local input is not implemented")
    
    av = _AV_shape(file_av)

    od_shape_inside, od_shape_outside = _AOI_shapes(file_shape, av)
    od_shape_inside['type_av'] = 'inside'
    od_shape_outside['type_av'] = 'outside'

    od_point_both = gpd.GeoDataFrame(
        pd.concat([od_shape_inside, od_shape_outside]),
        crs=CRS_PROJECTED, geometry="geometry"
    )
    od_point_both["area"] = od_point_both.area
    od_point_both['geometry'] = od_point_both.centroid

    # Add features: coordx, coordy
    od_point_both = od_point_both.to_crs(CRS_LATLONG)
    od_point_both[['lon', 'lat']] = od_point_both['geometry'].apply(
        lambda point: pd.Series([point.x, point.y])
    )
    od_point_both = od_point_both.to_crs(CRS_PROJECTED)
    od_point_both[['coordx', 'coordy']] = od_point_both['geometry'].apply(
        lambda point: pd.Series([point.x, point.y])
    )
    
    # Distinguish position and return & Reset index to avoid duplicate index issues
    ret_inside = od_point_both[od_point_both['type_av']=='inside'].reset_index(drop=True)
    ret_outside = od_point_both[od_point_both['type_av']=='outside'].reset_index(drop=True)
    
    return ret_inside, ret_outside

def prepare_otp_input_extended(file_centroids, file_shape, file_av, file_flows, local):
    '''
    Given the zones from the PUMS and the boundary of Area Verde, first it
    distinguishes between the zones inside and outside the area.
    Then, a new file is created with all outside zones as origin, and AV as destination
    TODO: do also the opposite, with AV as origin.
    '''

    od_point_in, od_point_out = read_and_prepare_centroids(file_centroids, file_shape, file_av, local)

    # Cross join
    od_point_in["_key"] = 1
    od_point_out["_key"] = 1
    df_cross = (
        pd.merge(od_point_out, od_point_in, on="_key", suffixes=("_from", "_to"))
        .drop("_key", axis=1)
        .rename(columns={'id_from': 'from', 'id_to': 'to'})
    )
    df_cross = df_cross[(df_cross["from"]!=df_cross["to"])]

    # Add flow info
    od_shapes = gpd.GeoDataFrame(pd.concat([od_point_in, od_point_out]), geometry="geometry")
    od_flow = _AOI_flows(file_flows, od_shapes)
    od_flow = od_flow[(od_flow["type_av_from"]=="outside")&(od_flow["type_av_to"]=="inside")].reset_index(drop=True)
    od_flow = od_flow.drop(columns={"type_av_from", "type_av_to"})
    od_flow = od_flow[(od_flow["from"]!=od_flow["to"])]

    df_cross["from"] = df_cross["from"].astype(int)
    df_cross["to"] = df_cross["to"].astype(int)
    df_cross = df_cross.merge(od_flow, how='left', on=['from', 'to'])
    # df_cross = df_cross[df_cross['flow']>=1]

    # Rename and return
    df_cross = (
        df_cross
        .rename(columns={'lat_from': 'origin_lat',
                        'lon_from': 'origin_lon',
                        'lat_to': 'dest_lat',
                        'lon_to': 'dest_lon'})
        [['origin_lat', 'origin_lon', 'from', 'dest_lat', 'dest_lon', 'to', 'flow']]
    )
    return df_cross
                             
def prepare_otp_input_simplified(file_centroids, file_shape, file_av, file_flows, local):
    '''
    Given the zones from the PUMS and the boundary of Area Verde, first it
    distinguishes between the zones inside and outside the area.
    The ones inside are merged and considered the unique Area Verde. 
    The ones outside remain as they are.
    Then, a new file is created with all outside zones as origin, and AV as destination
    TODO: do also the opposite, with AV as origin.
    '''

    df = prepare_otp_input_extended(file_centroids, file_shape, file_av, file_flows, local)
    od_points_in, _ = read_and_prepare_centroids(file_centroids, file_shape, file_av, local)
    point_av_lon, point_av_lat = find_av_centroid(od_points_in, df)
   
    # Dest point 
    df = df.groupby(["origin_lat", "origin_lon", "from"])["flow"].sum().reset_index()
    df['dest_lat'] = point_av_lat
    df['dest_lon'] = point_av_lon
    df["to"] = 0

    return df[['origin_lat', 'origin_lon', 'from', 'dest_lat', 'dest_lon', 'to', 'flow']]

def prepare_otp_input_inside_av(file_centroids, file_shape, file_av, file_flows, local):
    '''
    Given the zones from the PUMS and the boundary of Area Verde, first it
    distinguishes between the zones inside and outside the area. 
    The ones outside are discarded.
    Then, a new file is created with all combinations of inside zones as origin and destination
    '''

    od_point_in, od_point_out = read_and_prepare_centroids(file_centroids, file_shape, file_av, local)

    # Cross join
    od_point_in["_key"] = 1
    df_cross = (
        pd.merge(od_point_in, od_point_in,  on="_key", suffixes=("_from", "_to"))
        .drop("_key", axis=1)
        .rename(columns={"id_from": "from", "id_to": "to"})
    )
    df_cross = df_cross[df_cross["from"] < df_cross["to"]].reset_index(drop=True)
    df_cross = df_cross[(df_cross["from"]!=df_cross["to"])]

    # Add flow info
    od_shapes = gpd.GeoDataFrame(pd.concat([od_point_in, od_point_out]), geometry="geometry")
    od_flow = _AOI_flows(file_flows, od_shapes[["id", "area", "type_av"]])
    od_flow = od_flow[(od_flow["type_av_from"]=="inside")&(od_flow["type_av_to"]=="inside")].reset_index(drop=True)
    od_flow = od_flow.drop(columns={"type_av_from", "type_av_to"})
    od_flow = od_flow[(od_flow["from"]!=od_flow["to"])]

    df_cross["from"] = df_cross["from"].astype(int)
    df_cross["to"] = df_cross["to"].astype(int)
    df_cross = df_cross.merge(od_flow, how='left', on=['from', 'to'])
    # df_cross = df_cross[df_cross['flow']>=1]

    return (
        df_cross
        .rename(columns={'lat_from': 'origin_lat',
                        'lon_from': 'origin_lon',
                        'lat_to': 'dest_lat',
                        'lon_to': 'dest_lon'})
        [['origin_lat', 'origin_lon', 'from', 'dest_lat', 'dest_lon', 'to', 'flow']]
    )

def find_av_centroid(od_points_in, od_flow):

    # Flows
    df = od_flow.groupby(["dest_lat", "dest_lon", "to"])['flow'].sum().reset_index()
    od_points_in["id"] = od_points_in["id"].astype(int)
    df["to"] = df["to"].astype(int)
    df = df.merge(
        od_points_in[['id', 'coordx', 'coordy']].rename(columns={'id': 'to'}),
        on='to', how='inner'
    )

    # Weighted mean
    total_flow = df['flow'].sum()
    if total_flow == 0:
        return None, None

    df['weighted_coordx'] = df['flow'] / total_flow * df['coordx']
    df['weighted_coordy'] = df['flow'] / total_flow * df['coordy']

    coordx_mean = df['weighted_coordx'].sum()
    coordy_mean = df['weighted_coordy'].sum()

    mean_point = Point(coordx_mean, coordy_mean)
    mean_df = gpd.GeoDataFrame(
        [{'geometry': mean_point}], crs=CRS_PROJECTED
    ).to_crs(CRS_LATLONG)

    mean_df[['lon', 'lat']] = mean_df['geometry'].apply(
        lambda point: pd.Series([point.x, point.y])
    )

    return mean_df.loc[0, 'lon'], mean_df.loc[0, 'lat']

def _OD_shapes(
    namefile_polygons: str,
    namefile_centers: str | None = None
) -> gpd.GeoDataFrame:
    df = (
        gpd.read_file(namefile_polygons)
        .set_crs("EPSG:23032")
        .to_crs(CRS_PROJECTED)
        .rename(columns={"NO": "id"})
        .astype({"id": int, "TYPENO": int, "NAME": pd.StringDtype()})
    )
    df.columns = df.columns.str.lower()
    df["type2"] = "internal"

    if namefile_centers is not None:
        df_centers = _OD_centers(namefile_centers=namefile_centers)
        df_centers = df_centers[~(df_centers["id"].isin(df["id"]))]
        df_centers["geometry"] = df_centers.geometry.buffer(1000)
        df_centers["type2"] = "external"
        df = pd.concat([df, df_centers], ignore_index=True)
    return df

def _OD_centers(
    namefile_centers: str
) -> gpd.GeoDataFrame:
    df_centers = (
        gpd.read_file(namefile_centers)
        .set_crs("EPSG:23032")
        .to_crs(CRS_PROJECTED)
        .rename(columns={"NO": "id"})
        .astype({"id": int, "TYPENO": int, "NAME": pd.StringDtype()})
    )
    df_centers.columns = df_centers.columns.str.lower()
    df_centers['ratio_overlap'] = 0.0
    return df_centers

def _AV_shape(
    namefile: str
) -> gpd.GeoDataFrame:
    df = (
        gpd.read_file(namefile)
        .set_crs(CRS_LATLONG)
        .to_crs(CRS_PROJECTED)
    )
    return df

def _AOI_shapes(
    namefile: str,
    df_around: gpd.GeoDataFrame
):
    df = _OD_shapes(namefile_polygons=namefile)
    df_inside, df_outside = _AOI_OD_shapes(df, df_around)
    return df_inside, df_outside
    df = gpd.GeoDataFrame(
        pd.concat([df_inside, df_outside], axis=0)[["id", "name", "geometry"]], 
        geometry="geometry", 
        crs=df_inside.crs)

    df["id"] = df["id"].astype(str)
    df1 = gpd.overlay(df, df_around, how="intersection", keep_geom_type=True)
    df2 = gpd.overlay(df, df_around, how="difference", keep_geom_type=True)
    
    return df1, df2

def _AOI_OD_shapes(
    df_shapes: gpd.GeoDataFrame,
    df_around: gpd.GeoDataFrame,
):
    # Renaming
    df_shapes.loc[df_shapes['name'].isna(), 'name'] = df_shapes.loc[df_shapes['name'].isna(), 'code']
    df_shapes = df_shapes

    # RM overlapping zones
    aoi_inside = _remove_nonpartitioning_zones(df_shapes)
    aoi_inside = gpd.overlay(aoi_inside, df_around, how="intersection", keep_geom_type=True)

    aoi_outside = gpd.overlay(df_shapes, df_around, how="difference", keep_geom_type=True)
    aoi_outside = _remove_overlapping_zones(aoi_outside, overlap_threshold=0.99)
        
    return aoi_inside, aoi_outside

def _AOI_flows(
    namefile: str,
    od_shapes
) -> pd.DataFrame:
    # Read data
    df_od = (
        pd.read_excel(namefile)
        .rename(columns={'NumDaZona': 'from', 'NumAZona': 'to', 'ValMatr(1 Totale_H24)': 'flow'})
        .assign(flow = lambda x: x['flow'] * P2V)
        [['from', 'to', 'flow']]
    )
    df_od["from"] = df_od["from"].astype(int)
    df_od["to"] = df_od["to"].astype(int)
    od_shapes["id"] = od_shapes["id"].astype(int)
    df_od = df_od[(df_od["from"].isin(od_shapes["id"])) & df_od["to"].isin(od_shapes["id"])]
    # print("Original total flow: ", sum(df_od["flow"])) ## Debug only

    # Assign shapes and flows
    df_od = df_od.merge(
        od_shapes[["id", "area", "type_av"]].rename(columns={"id":"from", "area":"area_from", "type_av":"type_av_from"}),
        how='left',
        on="from",
        suffixes=["", "_from"]
    ).merge(
        od_shapes[["id", "area", "type_av"]].rename(columns={"id":"to", "area":"area_to", "type_av":"type_av_to"}),
        how='left',
        on="to",
        suffixes=["", "_to"]
    )
    df_od["flow"] = df_od["flow"].fillna(0)

    # Distribute flows between inside and outside AV
    df_od["flow"] = (
        df_od["flow"]
        * df_od["area_from"] / _sum_unique_area(df_od, "area_from", "from", "type_av_from")
        * df_od["area_to"] / _sum_unique_area(df_od, "area_to", "to", "type_av_to")
    ).fillna(0)

    # print("Final total flow: ", sum(df_od["flow"])) ## Debug only
    df_od["from"] = df_od["from"].astype(int)
    df_od["to"] = df_od["to"].astype(int)
    df_od = df_od[["from","type_av_from","to","type_av_to","flow"]]

    return df_od

def _remove_nonpartitioning_zones(
        df_shapes: gpd.GeoDataFrame, 
        coverage_threshold: float = 0.5,
        boundary_tolerance: float = 250.0
    ) -> gpd.GeoDataFrame:

    df = df_shapes.copy().reset_index(drop=True)
    
    # Ensure to take the exterior border
    total_union = df.geometry.unary_union
    if hasattr(total_union, 'exterior'):
        total_boundary = total_union.exterior
    elif hasattr(total_union, 'geoms'):
        from shapely.ops import unary_union as shapely_union
        exteriors = [geom.exterior for geom in total_union.geoms if hasattr(geom, 'exterior')]
        total_boundary = shapely_union(exteriors) if exteriors else total_union.boundary
    else:
        total_boundary = total_union.boundary
    
    # Find the zones to keep
    zones_to_keep = set()
    for i in range(len(df)):
        geom_i = df.geometry.iloc[i]
        boundary_i = geom_i.boundary
        total_boundary_length = boundary_i.length
        
        if total_boundary_length < boundary_tolerance:
            continue
        
        covered_length = 0.0
        # Coverage from the outer perimeter
        try:
            external_intersection = boundary_i.intersection(total_boundary)
            if hasattr(external_intersection, 'length'):
                covered_length += external_intersection.length
            elif hasattr(external_intersection, 'geoms'):
                covered_length += sum(
                    getattr(geom, 'length', 0) for geom in external_intersection.geoms
                    if hasattr(geom, 'length')
                )
        except:
            pass
        
        # Coverage from other zones' borders
        for j in range(len(df)):
            if i != j:
                boundary_j = df.geometry.iloc[j].boundary
                try:
                    intersection = boundary_i.intersection(boundary_j)
                    if hasattr(intersection, 'length'):
                        covered_length += intersection.length
                    elif hasattr(intersection, 'geoms'):
                        covered_length += sum(
                            getattr(geom, 'length', 0) for geom in intersection.geoms
                            if hasattr(geom, 'length')
                        )
                except:
                    continue
        
        coverage_ratio = covered_length / total_boundary_length
        
        if coverage_ratio >= coverage_threshold:
            zones_to_keep.add(i)
   
    return df.loc[list(zones_to_keep)].reset_index(drop=True)

def _remove_overlapping_zones(
        df: gpd.GeoDataFrame, 
        overlap_threshold: float = 0.05
    )-> gpd.GeoDataFrame:

    df = df.copy()
    df["area"] = df.geometry.area

    to_remove = set()

    for i, geom_i in df.geometry.items():
        if i in to_remove:
            continue

        inter_area_total = 0.0
        for j, geom_j in df.geometry.items():
            if i == j or j in to_remove:
                continue
            inter = geom_i.intersection(geom_j)
            if not inter.is_empty:
                inter_area_total += inter.area

        coverage_area_ratio = inter_area_total / df.at[i, "area"]

        if coverage_area_ratio > overlap_threshold:
            to_remove.add(i)

    return df.drop(index=to_remove).reset_index(drop=True)


def _sum_unique_area(df, area_col, id_col, type_col):
    return (
        df.drop_duplicates(subset=[id_col, type_col, area_col])  # rimuove duplicati reali
          .groupby(id_col)[area_col]
          .sum()
          .rename(f"{area_col}_all")
          .reindex(df[id_col])
          .values
    )

if __name__ == '__main__':
    print("Computing points from outside - extended") if verbose else None
    df_extended = prepare_otp_input_extended(file_centroids, file_shape, file_av, file_flows, local_raw)
    print("and saving.") if verbose else None
    file_output = "od-coords-extended"
    if local_input:
        put_dataframe(df_extended, name=f"input_od/{file_output}", type="parquet")
    else:
        log_dataframe(df_extended, name=file_output)
    
    print("Computing points from outside - simplified") if verbose else None
    df_simple = prepare_otp_input_simplified(file_centroids, file_shape, file_av, file_flows, local_raw)
    print("and saving.") if verbose else None
    file_output = "od-coords-simplified"
    if local_input:
        put_dataframe(df_simple, name=f"input_od/{file_output}", type="parquet")
    else:
        log_dataframe(df_simple, name=file_output)
    
    print("Computing points inside") if verbose else None
    df_av = prepare_otp_input_inside_av(file_centroids, file_shape, file_av, file_flows, local_raw)
    print("and saving.") if verbose else None
    file_output = "od-coords-av"
    if local_input:
        put_dataframe(df_av, name=f"input_od/{file_output}", type="parquet")
    else:
        log_dataframe(df_av, name=file_output)
    