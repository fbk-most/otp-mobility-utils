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
sys.path.append(f"{os.path.expanduser('..')}/src")
from utils import get_dataframe, put_dataframe, log_dataframe
from constants import CRS_LATLONG, CRS_PROJECTED, P2V
from params import local_raw, local_input

def read_and_prepare_centroids(file_centroids, file_shape, file_av, local):
    # Assign av to OD shapes
    if local:
        av = _AV_shape(file_av)
        od_shape = _OD_shapes(file_shape)
    else:
        NotImplementedError("Non-local input is not implemented")

    od_shape_inside, od_shape_outside = _OD_to_AV(df_od=od_shape, df_av=av)
    od_shape_inside['type_av'] = 'inside'
    od_shape_outside['type_av'] = 'outside'

    od_point_both = gpd.GeoDataFrame(
        pd.concat([od_shape_inside, od_shape_outside]),
        crs=CRS_PROJECTED, geometry="geometry"
    )
    od_point_both['geometry'] = od_point_both.centroid

    od_point = _OD_centers(file_centroids)
    od_point_outside_external = od_point[~od_point['id'].isin(od_shape['id'])]
    od_point_outside_external['type_av'] = 'outside'

    od_point_both = gpd.GeoDataFrame(
        pd.concat([od_point_outside_external, od_point_both]),
        crs=od_point.crs, geometry="geometry"
    )

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
    ret_inside = od_point_both[od_point_both['type_av']=='inside'].drop(columns='type_av').reset_index(drop=True)
    ret_outside = od_point_both[od_point_both['type_av']=='outside'].drop(columns='type_av').reset_index(drop=True)
    
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

    # Add flow info
    if local:
        od_flow = _OD_flows(file_flows)
    else:
        NotImplementedError("Non-local input is not implemented")
    df_cross = df_cross.merge(od_flow, how='inner', on=['from', 'to'])
    
    # Fix flows, filter non-relevant flows
    df_cross['flow'] = df_cross['flow'].fillna(0)
    df_cross['flow'] = df_cross['flow'] * df_cross['ratio_overlap_from'] * df_cross['ratio_overlap_to']
    df_cross = df_cross[df_cross['flow']>=1]

    return (
        df_cross
        .rename(columns={'lat_from': 'origin_lat',
                        'lon_from': 'origin_lon',
                        'lat_to': 'dest_lat',
                        'lon_to': 'dest_lon'})
        [['origin_lat', 'origin_lon', 'from', 'dest_lat', 'dest_lon', 'to', 'flow']]
    )
                             

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

    od_point_in, _ = read_and_prepare_centroids(file_centroids, file_shape, file_av, local)

    # Cross join
    od_point_in["_key"] = 1
    df_cross = (
        pd.merge(od_point_in, od_point_in,  on="_key", suffixes=("_from", "_to"))
        .drop("_key", axis=1)
        .rename(columns={"id_from": "from", "id_to": "to"})
    )
    df_cross = df_cross[df_cross["from"] < df_cross["to"]].reset_index(drop=True)

    # Add flow info
    if local:
        od_flow = _OD_flows(file_flows)
    else:
        NotImplementedError("Non-local input is not implemented")
    df_cross = df_cross.merge(od_flow, how='inner', on=['from', 'to'])
    
    # Fix flows, filter non-relevant flows
    df_cross['flow'] = df_cross['flow'].fillna(0)
    df_cross['flow'] = df_cross['flow'] * df_cross['ratio_overlap_from'] * df_cross['ratio_overlap_to']
    df_cross = df_cross[df_cross['flow']>=1]

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
    namefile_polygons: str
) -> gpd.GeoDataFrame:
    df = (
        gpd.read_file(namefile_polygons)
        .set_crs("EPSG:23032")
        .to_crs(CRS_PROJECTED)
        .rename(columns={"NO": "id"})
        .astype({"id": int, "TYPENO": int, "NAME": pd.StringDtype()})
    )
    df.columns = df.columns.str.lower()
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


def _OD_to_AV(
    df_od : gpd.GeoDataFrame, 
    df_av : gpd.GeoDataFrame, 
    overlap_threshold: float = 0.5
) -> list:
    df_od["area"] = df_od.area
    od_inside = (
        df_od
        .reset_index(drop=True)
        .overlay(df_av[["geometry"]], how="intersection")
    )
    od_inside['ratio_overlap'] = od_inside.area / od_inside['area']
    od_outside = (
        df_od
        .reset_index(drop=True)
        .overlay(df_av[["geometry"]], how="difference")
    )
    od_outside['ratio_overlap'] = od_outside.area / od_outside['area']

    return od_inside.drop(columns="area"), od_outside.drop(columns="area")


def _OD_flows(
    namefile: str
) -> pd.DataFrame:
    df_od = (
        pd.read_excel(namefile)
        .rename(columns={'NumDaZona': 'from', 'NumAZona': 'to', 'ValMatr(1 Totale_H24)': 'flow'})
        .assign(flow = lambda x: x['flow'] * P2V)
        [['from', 'to', 'flow']]
    )
    return df_od


if __name__ == '__main__':    
    df_extended = prepare_otp_input_extended(file_centroids, file_shape, file_av, file_flows, local_raw)
    file_output = "od-coords-extended"
    if local_input:
        put_dataframe(df_extended, name=f"input_od/{file_output}", type="parquet")
    else:
        log_dataframe(df_extended, name=file_output)
    
    df_simple = prepare_otp_input_simplified(file_centroids, file_shape, file_av, file_flows, local_raw)
    file_output = "od-coords-simplified"
    if local_input:
        put_dataframe(df_simple, name=f"input_od/{file_output}", type="parquet")
    else:
        log_dataframe(df_simple, name=file_output)
    
    df_av = prepare_otp_input_inside_av(file_centroids, file_shape, file_av, file_flows, local_raw)
    file_output = "od-coords-av"
    if local_input:
        put_dataframe(df_av, name=f"input_od/{file_output}", type="parquet")
    else:
        log_dataframe(df_av, name=file_output)
    
