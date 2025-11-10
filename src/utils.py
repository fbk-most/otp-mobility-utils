# SPDX-License-Identifier: Apache-2.0
import configparser
from pathlib import Path
import io
import pandas as pd
import geopandas as gpd
from pandas.core.interchange.dataframe_protocol import DataFrame
import boto3

import digitalhub as dh

PROJECT = "test-otp-v2"
PATH_TO_TESTDATA = Path(__file__).resolve().parent.parent / "data" 

def get_dataframe(name: str, local: bool = False) -> DataFrame:
    if local:
        return pd.read_parquet((PATH_TO_TESTDATA / name).with_suffix(".parquet"))
    return dh.get_dataitem(name, project=PROJECT).as_df()

def put_dataframe(df: pd.DataFrame, name: str, type: str = "parquet") -> str:
    path = PATH_TO_TESTDATA
    path.mkdir(parents=True, exist_ok=True)
    path = path / name
    match type:
        case "json":
            path = path.with_suffix(".json")
            df.to_json(path, orient="index", indent=4)
        case "csv":
            path = path.with_suffix(".csv")
            df.to_csv(path)
        case "parquet":
            path = path.with_suffix(".parquet")
            df.to_parquet(path)
        case _:
            raise NotImplementedError(f"Unsupported type: {type}")
    return str(path)

def log_dataframe(df: pd.DataFrame, name: str) -> None:
    project = dh.get_or_create_project(PROJECT)
    project.log_dataitem(name, "table", data=df)

def get_geojson(name: str, local: bool = False) -> gpd.GeoDataFrame:
    if local:
        return gpd.read_file((PATH_TO_TESTDATA / name).with_suffix(".geojson"))
    raise NotImplementedError

def put_geojson(gdf: gpd.GeoDataFrame, name: str) -> str:
    path = (PATH_TO_TESTDATA / name).with_suffix(".geojson")
    gdf.to_file(path, driver="GeoJSON")
    return str(path)

def log_geojson(gdf: gpd.GeoDataFrame, name: str) -> None:
    source = put_geojson(gdf, name)
    project = dh.get_or_create_project(PROJECT)
    project.log_artifact(name + ".geojson", "artifact", source=source)


def init_s3_local():
    """
    Initialize S3 connection for gdb analysis.
        Returns:
            s3: S3 resource object
            bucket: S3 bucket object
    NOTE: Specific to the platform and project setup.
    """
    endpoint_url="http://minio:9000"

    s3 = boto3.resource('s3',
                        endpoint_url=endpoint_url)

    bucket = s3.Bucket('datalake')
    return s3, bucket

def init_s3_dhcli(env = "gdb"):
    """
    Initialize S3 connection for overtourism analysis.
        Parameters:
            env: environment name
        Returns:
            s3: S3 resource object
            bucket: S3 bucket object
    NOTE: Specific to the DHCLI-based access to platform.
    """
    home = Path.home()

    config = configparser.ConfigParser()
    config.read(home / ".dhcore.ini")
    aws_endpoint_url = config[env]["aws_endpoint_url"]
    aws_access_key_id = config[env]["aws_access_key_id"]
    aws_secret_access_key = config[env]["aws_secret_access_key"]
    aws_session_token = config[env]["aws_session_token"]

    s3 = boto3.resource('s3',
                        endpoint_url=aws_endpoint_url,
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        aws_session_token=aws_session_token)


    bucket = s3.Bucket('datalake')
    return s3, bucket

s3, bucket = None, None

def init_s3(force = False):
    global s3, bucket
    if s3 is None or bucket is None or force:
        # s3, bucket = init_s3_dhcli("gdb")
        s3, bucket = init_s3_local()
    return s3, bucket

def get_s3(name: str):
    s3, bucket = init_s3()
    object = s3.Object('datalake', 'test-otp-v2/' + name)

    buffer = io.BytesIO()
    object.download_fileobj(buffer)
    buffer.seek(0)
    return buffer