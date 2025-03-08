"""
merge_data.py

This script processes and merges data from multiple sources, including GreatSchools scraping data,
sentiment analysis results, result from geographic converter and intergenerational mobility data.

Author: Carrie Huang, Jeanette Wu, Kunjian Li, Shirley Zhang

We disclose that we employed Claude to integrate comprehensive logging and robust error-handling mechanisms,
thereby enhancing the script's overall reliability. Additionally, we encapsulated the script within a class
to improve its modularity and reusability.

"""

import pandas as pd
import numpy as np
import os
import ast

class MobilityDataProcessor:
    def __init__(self):
        """
        Initializes the MobilityDataProcessor class.
        No variables are defined yet; they will be created
        once run_all() is called.
        """
        pass

    def run_all(self):
        """
        Executes all data loading, cleaning, merging, and aggregation steps.
        The final DataFrames are stored as attributes of this class.
        """
        

        
        # Setup and file paths

        current_dir = os.path.dirname(os.path.realpath(__file__))

        # one table from the intergenerational mobility dataset. 
        cz_file_path = os.path.join(current_dir, "data", "mobility_cz.csv")
        # another table from the intergenerational mobility dataset.
        county_file_path = os.path.join(current_dir, "data", "mobility_county.csv")
        # table with county information from the intergenerational mobility dataset.
        cz_info_file_path = os.path.join(current_dir, "data", "county_info.csv")
        # table we created from coverter.py
        school_tract_cz_file_path = os.path.join(current_dir, "data", "links", "school_tract_cz_merged.csv")
        
        # Load data

        mobility_cz = pd.read_csv(cz_file_path)
        mobility_county = pd.read_csv(county_file_path)
        cz_info = pd.read_csv(cz_info_file_path)
        school_tract_cz = pd.read_csv(school_tract_cz_file_path)

        # Rename columns in mobility_cz
        mobility_cz.rename(columns={
            'AM, 80-82 Cohort': 'Absolute_Upward_Mobility',
            'CZ': 'CZ_ID'
        }, inplace=True)

        # Merge commuting zone mobility with school_tract_cz

        mobility_cz['CZ_ID'] = mobility_cz['CZ_ID'].astype(str).str.strip()
        school_tract_cz['CZ_ID'] = school_tract_cz['CZ_ID'].astype(str).str.strip()

        # Zero-fill (5-digit CZ_IDs)
        mobility_cz['CZ_ID'] = mobility_cz['CZ_ID'].str.zfill(5)
        school_tract_cz['CZ_ID'] = school_tract_cz['CZ_ID'].str.zfill(5)

        self.cz_mobility_df = school_tract_cz.merge(
            mobility_cz[['CZ_ID', 'Absolute_Upward_Mobility']], 
            on='CZ_ID', 
            how='left'
        )

        # Merge county mobility rate with school_tract_cz

        mobility_county.rename(columns={
            'Absolute Upward Mobility': 'Absolute_Upward_Mobility',
            'County FIPS Code': 'County_FIPS'
        }, inplace=True)

        # Drop a header row if it exists (the original code drops index=0)
        mobility_county = mobility_county.drop(index=0)

        mobility_county['County_FIPS'] = mobility_county['County_FIPS'].astype(str).str.strip()
        school_tract_cz['County_FIPS'] = school_tract_cz['County_FIPS'].astype(str).str.strip()

        # Zero-fill (assuming 5-digit county FIPS)
        mobility_county['County_FIPS'] = mobility_county['County_FIPS'].str.zfill(5)
        school_tract_cz['County_FIPS'] = school_tract_cz['County_FIPS'].str.zfill(5)

        self.county_mobility_df = school_tract_cz.merge(
            mobility_county[['County_FIPS', 'Absolute_Upward_Mobility']], 
            on='County_FIPS', 
            how='left'
        )

        # Drop rows where mobility is missing
        self.county_mobility_df = self.county_mobility_df.dropna(subset=['Absolute_Upward_Mobility'])


        # Scraped reviews with sentiment score from GreatSchools
        review_path = os.path.join(current_dir, "data", "greatschools", "review_data_all_states.csv")
        # Scraped ratings and description from GreatSchools
        school_path = os.path.join(current_dir, "data", "greatschools", "scraped_ratings_all_states.csv")
        
        review_df = pd.read_csv(review_path)
        schools_df = pd.read_csv(school_path)

        schools_df.rename(columns={'school_id': 'universal-id'}, inplace=True)
        review_df.rename(columns={'universal_id': 'universal-id'}, inplace=True)

        schools_df = schools_df.merge(
            review_df[['universal-id', 'sentiment_scores']],
            on='universal-id',
            how='left'
        )

        # Clean up sentiment_scores
        def clean_sentiment(x):
            """
            Convert sentiment_scores (dict) to 4 columns.
            """
            if isinstance(x, dict):
                return x
            elif isinstance(x, str):
                try:
                    return ast.literal_eval(x)
                except:
                    return {'neg': 0, 'neu': 0, 'pos': 0, 'compound': 0}
            elif pd.isna(x):
                return {'neg': 0, 'neu': 0, 'pos': 0, 'compound': 0}
            else:
                return {'neg': 0, 'neu': 0, 'pos': 0, 'compound': 0}

        schools_df['sentiment_scores'] = schools_df['sentiment_scores'].apply(clean_sentiment)
        sentiment_df = schools_df['sentiment_scores'].apply(pd.Series)
        schools_df = pd.concat([schools_df, sentiment_df], axis=1)


        # Aggregate to CZ Level

        # Merge in the CZ_ID from school_tract_cz
        schools_df = schools_df.merge(
            school_tract_cz[['universal-id', 'CZ_ID']],
            on='universal-id',
            how='left'
        )

        # Define aggregation
        aggregation_rules = {}
        for col in schools_df.columns:
            if col == 'CZ_ID':
                continue
            elif schools_df[col].dtype == 'object':
                aggregation_rules[col] = 'first'
            else:
                aggregation_rules[col] = 'mean'

        cz_df = schools_df.groupby('CZ_ID').agg(aggregation_rules).reset_index()

        # Drop some columns
        cz_df.drop(columns=['universal-id', 'sentiment_scores'], inplace=True)

        # Merge with mobility_cz
        cz_df = cz_df.merge(mobility_cz[['CZ_ID', 'Absolute_Upward_Mobility']], on='CZ_ID', how='left')
        self.cz_df = cz_df

        # Aggregate to county Level
        school_df2 = schools_df.merge(
            school_tract_cz[['universal-id', 'County_FIPS']],
            on='universal-id',
            how='left'
        )

        # Define aggregation
        aggregation_rules = {}
        for col in school_df2.columns:
            if col == 'County_FIPS':
                continue
            elif school_df2[col].dtype == 'object':
                aggregation_rules[col] = 'first'
            else:
                aggregation_rules[col] = 'mean'

        county_df = school_df2.groupby('County_FIPS').agg(aggregation_rules).reset_index()
        county_df.drop(columns=['universal-id', 'sentiment_scores'], inplace=True)

        county_df = county_df.merge(
            mobility_county[['County_FIPS', 'Absolute_Upward_Mobility']], 
            on='County_FIPS', 
            how='left'
        )

        # Map county_fips with state
        state_map = {17: 'IL', 55: 'WI', 18: 'IN'}
        county_df['state_fips'] = county_df['County_FIPS'].astype(int) // 1000
        county_df['state'] = county_df['state_fips'].map(state_map)
        county_df.drop(columns=['state_fips'], inplace=True)
        self.county_df = county_df  # store it in the class

        # Merge county_df with cz_info (population)

        cz_info.rename(columns={
            'CZ': 'CZ_ID',
            'Census 2000 population': 'population'
        }, inplace=True)

        # Merge population into county_df
        county_df = county_df.merge(
            cz_info[['CZ_ID', 'population']],
            on='CZ_ID',
            how='left'
        )

        # Convert population to int
        county_df['population'] = county_df['population'].str.replace(',', '').astype(int)

        # Compute population-weighted average at CZ level (from county data)

        aggregation_rules = {}
        for col in county_df.columns:
            # Skip certain columns
            if col in ['County_FIPS', 'state', 'County Name', 'CZ_ID', 'population', 'Absolute_Upward_Mobility']:
                continue
            elif county_df[col].dtype == 'object':
                aggregation_rules[col] = 'first'
            else:
                aggregation_rules[col] = 'mean'

        cz_df_from_county = county_df.groupby('CZ_ID').agg(aggregation_rules).reset_index()

        # Keep some columns
        cz_df_from_county = county_df[['CZ_ID', 'population', 'state', 'Absolute_Upward_Mobility']].merge(
            cz_df_from_county, on='CZ_ID', how='left'
        )
        self.cz_df_from_county = cz_df_from_county

        # Save results as CSV: 
        # output are in the data folder
        # Results are saved for data analysis and visualization

        cz_df.to_csv(
            "/Users/huangyiyang/Desktop/Winter_2025/MACS30122/final-project-ascending(feb 26)/data/cz_edu_mob.csv",
            index=False
            )
        county_df.to_csv(
            "/Users/huangyiyang/Desktop/Winter_2025/MACS30122/final-project-ascending(feb 26)/data/county_edu_mob.csv",
            index=False
            )
        cz_df_from_county.to_csv(
            "/Users/huangyiyang/Desktop/Winter_2025/MACS30122/final-project-ascending(feb 26)/data/cz_from_county_edu_mob.csv",
            index=False
            )

        # Now everything is stored in self.<variable_name>
        print("run_all() complete. DataFrames stored as:")
        print("  self.cz_mobility_df")
        print("  self.county_mobility_df")
        print("  self.cz_df")
        print("  self.county_df")
        print("  self.cz_df_from_county")
