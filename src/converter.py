#!/usr/bin/env python3
"""
School Data Consolidation Script

This script takes school data and links it to tract and commuting zone data for further analysis.

Created by Shirley Zhang

"""



import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os
from typing import Tuple

def setup_file_paths() -> Tuple[str, str, str, str]:
    """
    Set up the file paths for all required input files.
    
    Returns:
        Tuple containing paths for school data, tract demographics, tract geometry, and CZ ID files
    """
    current_dir = os.getcwd()
    
    # Define file names
    school_file = "schools_data_all_states.csv"
    tracts_demo_file = "cz_2010_revised_urban_rural.xlsx"
    tracts_geo_file = "cb_2018_17_tract_500k.shp"
    cz_id_file = "cz_equivalency.xls"
    
    # Create file paths
    school_file_path = os.path.join(current_dir, 'data','greatschools', school_file)
    geo_dir = os.path.join(current_dir, "data", 'geo')
    tracts_demo_path = os.path.join(geo_dir, tracts_demo_file)
    tracts_geo_path = os.path.join(geo_dir, tracts_geo_file)
    cz_id_path = os.path.join(geo_dir, cz_id_file)
    
    return school_file_path, tracts_demo_path, tracts_geo_path, cz_id_path

def load_school_data(school_file_path: str) -> gpd.GeoDataFrame:
    """
    Load school data and convert it to a GeoDataFrame.
    
    Args:
        school_file_path: Path to the school data CSV file
    
    Returns:
        GeoDataFrame containing school geometry
    """
    school_df = pd.read_csv(school_file_path)
    school_gdf = gpd.GeoDataFrame(
        school_df,
        geometry=gpd.points_from_xy(school_df.lon, school_df.lat),
        crs="EPSG:4326"
    )
    return school_gdf[['geometry','universal-id']].copy()

def load_tract_data(tracts_geo_path: str) -> gpd.GeoDataFrame:
    """
    Load tract geometric data.
    
    Args:
        tracts_geo_path: Path to the tract geometry shapefile
    
    Returns:
        GeoDataFrame containing tract identifiers and geometry
    """
    tracts_gdf = gpd.read_file(tracts_geo_path)
    return tracts_gdf[['GEOID', 'geometry']].copy()

def link_school_to_tract(school_identifier: gpd.GeoDataFrame, 
                        tracts_identifier: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Link schools to tracts by finding the nearest tract to each school.
    
    Args:
        school_identifier: GeoDataFrame containing school locations
        tracts_identifier: GeoDataFrame containing tract geometries
    
    Returns:
        GeoDataFrame with schools linked to their nearest tract
    """
    # Store original universal-id and geometry relationship
    original_data = school_identifier[['universal-id', 'geometry']].copy()
    
    # Create representative points for tracts
    tracts_identifier['inside_point'] = tracts_identifier.geometry.representative_point()
    tracts_identifier['geometry_tract'] = tracts_identifier.geometry
    tracts_identifier["geometry"] = tracts_identifier["inside_point"]
    
    # Reproject to appropriate CRS for USA
    tracts_identifier = tracts_identifier.to_crs(epsg=5070)
    school_geometry = school_identifier[['geometry']].to_crs(epsg=5070)
    
    # Find nearest tract using only geometry
    school_tracts_id = gpd.sjoin_nearest(
        school_geometry, 
        tracts_identifier, 
        how="left", 
        distance_col="distance"
    )
    
    # Add back the universal-id by index
    school_tracts_id['universal-id'] = original_data['universal-id']
    
    school_tracts_id.rename(columns={'GEOID': 'Tract_FIPS'}, inplace=True)
    return school_tracts_id

def load_demographic_data(tracts_demo_path: str) -> pd.DataFrame:
    """
    Load tract demographic data.
    
    Args:
        tracts_demo_path: Path to the tract demographics Excel file
    
    Returns:
        DataFrame containing tract FIPS codes and state information
    """
    tracts_df = pd.read_excel(tracts_demo_path, header=1)
    tracts_df.rename(columns={'State-County FIPS Code': 'FIPS'}, inplace=True)
    return tracts_df[['FIPS', 'Select State',
                      'State-County-Tract FIPS Code (lookup by address at http://www.ffiec.gov/Geocode/)']].copy()

def load_cz_data(cz_id_path: str) -> pd.DataFrame:
    """
    Load commuting zone ID data.
    
    Args:
        cz_id_path: Path to the CZ ID Excel file
    
    Returns:
        DataFrame containing commuting zone IDs and FIPS codes
    """
    cz_id_df = pd.read_excel(cz_id_path, header=0)
    return cz_id_df[['Commuting Zone ID, 1990', 'FIPS']].copy()

def link_tract_to_cz(tracts_fips: pd.DataFrame, cz_id: pd.DataFrame) -> pd.DataFrame:
    """
    Link tracts to commuting zones and filter for specific states.
    
    Args:
        tracts_fips: DataFrame containing tract FIPS codes
        cz_id: DataFrame containing commuting zone IDs
    
    Returns:
        DataFrame with tracts linked to commuting zones
    """
    # Merge tracts and commuting zones
    tracts_cz_merged_df = pd.merge(tracts_fips, cz_id, on='FIPS', how='left')
    
    # Filter for specific states
    states_filter = tracts_cz_merged_df['Select State'].isin(['IL', 'IN', 'WI', 'MI'])
    tracts_cz_merged_df = tracts_cz_merged_df[states_filter]
    
    # Convert CZ ID to integer
    tracts_cz_merged_df['Commuting Zone ID, 1990'] = tracts_cz_merged_df['Commuting Zone ID, 1990'].astype(int)
    
    # Reorder and rename columns
    new_order = ['Select State', 'Commuting Zone ID, 1990', 'FIPS',
                 'State-County-Tract FIPS Code (lookup by address at http://www.ffiec.gov/Geocode/)']
    tracts_cz_merged_df = tracts_cz_merged_df.reindex(columns=new_order)
    
    column_rename = {
        'Select State': 'State',
        'Commuting Zone ID, 1990': 'CZ_ID',
        'FIPS': 'County_FIPS',
        'State-County-Tract FIPS Code (lookup by address at http://www.ffiec.gov/Geocode/)': 'Tract_FIPS'
    }
    tracts_cz_merged_df.rename(columns=column_rename, inplace=True)
    
    return tracts_cz_merged_df

def main():
    """Main function to execute the data processing pipeline."""
    try:
        # Setup file paths
        school_file_path, tracts_demo_path, tracts_geo_path, cz_id_path = setup_file_paths()
        
        # Load and process school data
        school_identifier = load_school_data(school_file_path)
        
        # Load and process tract data
        tracts_identifier = load_tract_data(tracts_geo_path)
        
        # Link schools to tracts
        school_tracts = link_school_to_tract(school_identifier, tracts_identifier)
        print("Successfully linked schools to tracts")
        
        # Load demographic and CZ data
        tracts_fips = load_demographic_data(tracts_demo_path)
        cz_id = load_cz_data(cz_id_path)
        
        # Link tracts to commuting zones
        tracts_cz = link_tract_to_cz(tracts_fips, cz_id)
        print("Successfully linked tracts to commuting zones")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.getcwd()), 'data', 'links')
        os.makedirs(output_dir, exist_ok=True)

        # Save school-tract linkage results
        school_tracts_output = os.path.join(output_dir, 'school_tract_linkage.csv')
        school_tracts.to_csv(school_tracts_output, index=False)
        print(f"Saved school-tract linkage to {school_tracts_output}")

        # Save tract-commuting zone linkage results
        tracts_cz_output = os.path.join(output_dir, 'tract_cz_linkage.csv')
        tracts_cz.to_csv(tracts_cz_output, index=False)
        print(f"Saved tract-commuting zone linkage to {tracts_cz_output}")

        # Print data types to verify
        print("School-tract linkage Tract_FIPS dtype:", school_tracts['Tract_FIPS'].dtype)
        print("Tract-CZ linkage Tract_FIPS dtype:", tracts_cz['Tract_FIPS'].dtype)
        
        # Convert Tract_FIPS to string in both dataframes before merging
        school_tracts['Tract_FIPS'] = school_tracts['Tract_FIPS'].astype(str)
        tracts_cz['Tract_FIPS'] = tracts_cz['Tract_FIPS'].astype(str)
        
        # Merge the two files
        merged_data = pd.merge(
            school_tracts,
            tracts_cz,
            on='Tract_FIPS',
            how='left'
        )
        
        # Print merge result info
        print(f"Original school_tracts rows: {len(school_tracts)}")
        print(f"Original tracts_cz rows: {len(tracts_cz)}")
        print(f"Merged data rows: {len(merged_data)}")
        
        # Save merged results
        merged_output = os.path.join(output_dir, 'school_tract_cz_merged.csv')
        merged_data.to_csv(merged_output, index=False)
        print(f"Saved merged data to {merged_output}")
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}")
    except Exception as e:
        print(f"Error occurred during processing: {e}")

if __name__ == "__main__":
    main()