import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

CRS_LATLONG = "EPSG:4326"
CRS_PROJECTED = "EPSG:6875"
P2V = 0.6265460762750291


def read_and_prepare_centroids(file_centroids, file_shape, file_av):
    # Assign av to OD shapes
    av = _AV_shape(file_av)
    od_shape = _OD_shapes(file_shape)
    od_shape = _OD_to_AV(df_od=od_shape, df_av=av)

    # Merge and filter: OD centers only internal
    od_point = _OD_centers(file_centroids)
    od_point = od_point.merge(
        od_shape[['id', 'in_av']], how='inner', on='id'
    )

    # Add features: coordx, coordy
    od_point = od_point.to_crs(CRS_LATLONG)
    od_point[['lon', 'lat']] = od_point['geometry'].apply(
        lambda point: pd.Series([point.x, point.y])
    )
    od_point = od_point.to_crs(CRS_PROJECTED)
    od_point[['coordx', 'coordy']] = od_point['geometry'].apply(
        lambda point: pd.Series([point.x, point.y])
    )
    
    # Distinguish position and return
    od_points_in = od_point[od_point['in_av']].drop(columns='in_av')
    od_points_out = od_point[~od_point['in_av']].drop(columns='in_av')
    return od_points_in, od_points_out


def prepare_otp_input(file_centroids, file_shape, file_av, file_flows):

    od_points_in, od_points_out = read_and_prepare_centroids(file_centroids, file_shape, file_av)
    point_dest_lon, point_dest_lat = find_av_centroid(od_points_out, od_points_in, file_flows)
    # Origin point
    df = od_points_out[['lat', 'lon', 'id']].rename(
        columns={'lat':'origin_lat', 'lon':'origin_lon', 'id': 'from'})

    # Dest point 
    df['dest_lat'] = point_dest_lat
    df['dest_lon'] = point_dest_lon

    # Add flow info
    od_flow = _OD_flows(file_flows)
    od_flow = od_flow[(od_flow['from'].isin(od_points_out['id'])) & 
                      (od_flow['to'].isin(od_points_in['id']))]
    od_flow = od_flow.groupby('from')['flow'].sum().reset_index()
    df = df.merge(
        od_flow, how='left', on='from'
    )
    df['flow'] = df['flow'].fillna(0)

    return df


def find_av_centroid(od_points_out, od_points_in, file_flows):

    # Add flow
    od_flow = _OD_flows(file_flows)
    od_flow = od_flow[(od_flow['from'].isin(od_points_out['id'])) & 
                    (od_flow['to'].isin(od_points_in['id']))]
    od_flow = od_flow.groupby('to')['flow'].sum().reset_index()
    df = od_points_in.merge(
        od_flow.rename(columns={'to': 'id'}), how='left', on='id'
    )
    df['flow'] = df['flow'].fillna(0)

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
) -> gpd.GeoDataFrame:
    df_od["area"] = df_od.area
    areas_intersects = (
        df_od
        .reset_index(drop=True)
        .overlay(df_av[["geometry"]], how="intersection")
    )
    ratio_overlap = areas_intersects.area / areas_intersects['area']

    id_ok = areas_intersects[ratio_overlap > overlap_threshold]['id'].values
    df_od['in_av'] = False
    df_od.loc[df_od['id'].isin(id_ok), 'in_av'] = True

    return df_od


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
    file_centroids = "data/input_od/Shape_zone_centroid.SHP"
    file_shape = "data/input_od/Shape_zone.SHP"
    file_av = "data/input_od/area_verde_manual_v1.geojson"
    file_flows = "data/input_od/PROGETTO-OD.xlsx"
    df = prepare_otp_input(file_centroids, file_shape, file_av, file_flows)
    
    file_output = "data/input_od/OD_coordinates_v2.parquet"
    df.head(10).to_parquet(file_output)
