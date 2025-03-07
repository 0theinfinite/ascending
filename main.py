#!/usr/bin/env python3
"""
main.py

A simplified main script for the Ascending Project.
This demo runs the workflow steps in sequence:
  1. School Data Collection
  2. Review Collection & Sentiment Analysis
  3. School Ratings Collection
  4. Geographic Data Conversion
  5. Data Merging
  6. Regression Analysis

Authors: Carrie Huang, Jeanette Wu, Kunjian Li, Shirley Zhang
"""

import os
import logging
from datetime import datetime
import pandas as pd

# Import key functions/classes from project modules
from src.collect_schools import SchoolDataCollector, Config as SchoolConfig
from src.collect_reviews import SchoolReviewsScraper
from src.quantity_scraper import SchoolScraper
from src.converter import (setup_file_paths, load_school_data, load_tract_data, 
                           link_school_to_tract, load_demographic_data, load_cz_data, link_tract_to_cz)
from src.merge_data import MobilityDataProcessor
from src.regression import remove_highly_correlated_features

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'ascending_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Welcome to the Ascending Project!")
    
    # 1. Collect School Data
    logger.info("Step 1: Collecting school data from GreatSchools...")
    config = SchoolConfig()
    collector = SchoolDataCollector(config)
    collector.collect_all_states(level_codes=config.LEVEL_CODES)
    logger.info("School data collection complete.\n")
    
    # 2. Collect Reviews & Perform Sentiment Analysis
    logger.info("Step 2: Collecting reviews and analyzing sentiment...")
    current_dir = os.path.dirname(os.path.realpath(__file__))
    input_csv = os.path.join(current_dir, 'data', 'greatschools', 'schools_data_all_states.csv')
    output_csv = os.path.join(current_dir, 'data', 'greatschools', 'review_data_all_states.csv')
    reviews_scraper = SchoolReviewsScraper(log_frequency='minimal')
    reviews_scraper.process_schools_csv(input_csv, output_csv)
    logger.info("Review collection complete.\n")
    
    # 3. Collect School Ratings
    logger.info("Step 3: Collecting school ratings...")
    ratings_scraper = SchoolScraper()
    ratings_scraper.run()
    logger.info("Ratings collection complete.\n")
    
    # 4. Convert Geographic Data
    logger.info("Step 4: Converting geographic data...")
    school_file_path, tracts_demo_path, tracts_geo_path, cz_id_path = setup_file_paths()
    school_identifier = load_school_data(school_file_path)
    tracts_identifier = load_tract_data(tracts_geo_path)
    school_tracts = link_school_to_tract(school_identifier, tracts_identifier)
    tracts_fips = load_demographic_data(tracts_demo_path)
    cz_id = load_cz_data(cz_id_path)
    tracts_cz = link_tract_to_cz(tracts_fips, cz_id)
    
    # Save intermediate geographic linkages
    links_dir = os.path.join(current_dir, 'data', 'links')
    os.makedirs(links_dir, exist_ok=True)
    school_tracts.to_csv(os.path.join(links_dir, 'school_tract_linkage.csv'), index=False)
    tracts_cz.to_csv(os.path.join(links_dir, 'tract_cz_linkage.csv'), index=False)
    merged_data = pd.merge(school_tracts, tracts_cz, on='Tract_FIPS', how='left')
    merged_data.to_csv(os.path.join(links_dir, 'school_tract_cz_merged.csv'), index=False)
    logger.info("Geographic data conversion complete.\n")
    
    # 5. Merge Datasets
    logger.info("Step 5: Merging all datasets...")
    processor = MobilityDataProcessor()
    processor.run_all()
    logger.info("Dataset merging complete.\n")
    
    # 6. Run Regression Analysis
    logger.info("Step 6: Running regression analysis...")
    # For presentation, we demonstrate feature selection on county-level data.
    current_dir = os.path.dirname(os.path.realpath(__file__))
    county_file = os.path.join(current_dir, 'data', 'county_edu_mob.csv')
    df_county = pd.read_csv(county_file).dropna(subset=['Absolute_Upward_Mobility'])
    
    # Prepare county data for analysis
    X_county = df_county.drop(columns=['Absolute_Upward_Mobility', 'CZ_ID', 'state']).set_index('County_FIPS')
    X_county = X_county.select_dtypes(exclude=['object']).replace([float('inf'), float('-inf')], float('nan')).fillna(0)
    y_county = df_county[['Absolute_Upward_Mobility']].set_index(df_county['County_FIPS'])
    to_drop = remove_highly_correlated_features(X_county, y_county['Absolute_Upward_Mobility'], 0.7)
    X_county_selected = X_county.drop(columns=to_drop)
    logger.info(f"County-level selected features: {list(X_county_selected.columns)}")
    logger.info("Regression analysis complete.\n")
    
    logger.info("Ascending Project pipeline completed successfully!")
    print("\nWelcome to the Ascending Project!")
    print("All steps executed. Check log files and output directories for results.")

if __name__ == "__main__":
    main()
