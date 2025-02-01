#!/usr/bin/env python3
"""
School Data Collection Script

This script fetches school information from the GreatSchools API for specified states
and their zip codes, saving the data to separate CSV files by state.
"""

import requests
import pandas as pd
import time
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    STATES = ['MI', 'IN', 'IL', 'WI']  # List of states to process
    API_KEY = 'YOURAPIHERE'
    ZIP_CODES_PATH = 'data/zip_codes.csv'
    API_BASE_URL = "https://gs-api.greatschools.org/v2/schools?"
    REQUEST_DELAY = 0.1  # Delay between API requests in seconds
    SCHOOLS_PER_PAGE = 50
    OUTPUT_DIR = Path('output')

class SchoolDataCollector:
    def __init__(self, config: Config):
        """Initialize the SchoolDataCollector with configuration."""
        self.config = config
        self.headers = {
            'Accept': 'application/json',
            'Content': 'application/json',
            'X-API-Key': self.config.API_KEY
        }
        # Create output directory if it doesn't exist
        self.config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def load_zip_codes(self, state: str) -> list:
        """
        Load and filter zip codes for the specified state.
        
        Args:
            state: State abbreviation (e.g., 'IL')
            
        Returns:
            list: List of zip codes for the specified state
        """
        try:
            zip_codes = pd.read_csv(self.config.ZIP_CODES_PATH)
            return zip_codes[zip_codes['state'] == state]['zip'].tolist()
        except FileNotFoundError:
            logger.error(f"Zip codes file not found at {self.config.ZIP_CODES_PATH}")
            raise
        except Exception as e:
            logger.error(f"Error loading zip codes for state {state}: {str(e)}")
            raise

    def fetch_schools_by_zip(self, zip_code: str, level_codes: str = 'm') -> Optional[Dict[str, Any]]:
        """
        Fetch schools by zip code and level codes.
        
        Args:
            zip_code: ZIP code to search
            level_codes: School level codes (default: 'm' for middle school)
            
        Returns:
            Optional[Dict]: JSON response or None if no schools found
        """
        query_params = f'zip={zip_code}&level_codes={level_codes}&limit={self.config.SCHOOLS_PER_PAGE}'
        query_url = self.config.API_BASE_URL + query_params

        try:
            response = requests.get(
                query_url, 
                headers=self.headers, 
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if not data.get('schools'):
                logger.info(f"No schools found for ZIP code {zip_code}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data for ZIP {zip_code}: {str(e)}")
            return None

    def collect_state_data(self, state: str) -> pd.DataFrame:
        """
        Collect school data for a specific state.
        
        Args:
            state: State abbreviation to collect data for
            
        Returns:
            pd.DataFrame: Collected school data for the state
        """
        schools_df = pd.DataFrame()
        zip_codes = self.load_zip_codes(state)
        total_zips = len(zip_codes)
        
        logger.info(f"Starting collection for state {state} with {total_zips} ZIP codes")
        
        for i, zip_code in enumerate(zip_codes, 1):
            logger.info(f"Processing {state} ZIP {zip_code} ({i}/{total_zips})")
            
            response = self.fetch_schools_by_zip(zip_code)
            if response is not None:
                zip_school = pd.DataFrame(response['schools'])
                zip_school['zip'] = zip_code
                zip_school['state'] = state
                schools_df = pd.concat([schools_df, zip_school], ignore_index=True)
            
            time.sleep(self.config.REQUEST_DELAY)
        
        return schools_df

    def collect_all_states(self) -> Dict[str, pd.DataFrame]:
        """
        Collect data for all configured states.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping state codes to their school data
        """
        state_data = {}
        
        for state in self.config.STATES:
            logger.info(f"Starting collection for state: {state}")
            state_df = self.collect_state_data(state)
            
            # Save state data to CSV
            output_path = self.config.OUTPUT_DIR / f'schools_data_{state.lower()}.csv'
            state_df.to_csv(output_path, index=False)
            logger.info(f"Saved {state} data to {output_path}")
            
            state_data[state] = state_df
        
        # Create a combined dataset
        combined_df = pd.concat(state_data.values(), ignore_index=True)
        combined_path = self.config.OUTPUT_DIR / 'schools_data_all_states.csv'
        combined_df.to_csv(combined_path, index=False)
        logger.info(f"Saved combined data to {combined_path}")
        
        return state_data

def main():
    """Main execution function."""
    try:
        config = Config()
        collector = SchoolDataCollector(config)
        state_data = collector.collect_all_states()
        
        # Print summary statistics
        for state, df in state_data.items():
            logger.info(f"Collected {len(df)} schools for {state}")
            
    except Exception as e:
        logger.error(f"Script execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()