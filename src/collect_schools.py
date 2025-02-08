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
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    STATES = ['MI', 'IN', 'IL', 'WI']  # List of states to process
    LEVEL_CODES = 'm|h'  # Middle and high schools, use None to fetch all levels
    API_KEY = 'kICbx7Ja0naaVKCG0y4dG6sT86dWH1vA5UdyG2YI'
    ZIP_CODES_PATH = 'data/geo/zip_codes.csv'
    API_BASE_URL = "https://gs-api.greatschools.org/v2/schools?"
    REQUEST_DELAY = 0.1  # Delay between API requests in seconds
    SCHOOLS_PER_PAGE = 50
    OUTPUT_DIR = Path('data/greatschools')

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

    def fetch_schools_by_zip(self, zip_code: str, level_codes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch schools by zip code and optional level codes, handling pagination.
        """
        all_schools = []
        page = 0
        
        while True:
            # Build query parameters
            params = {
                'zip': zip_code,
                'limit': self.config.SCHOOLS_PER_PAGE,
                'page': page
            }
            
            # Add level_codes to params if specified
            if level_codes:
                params['level_codes'] = level_codes
            
            # Construct query string using params dictionary
            query_string = '&'.join(f"{k}={v}" for k, v in params.items())
            url = f"{self.config.API_BASE_URL}{query_string}"
            
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get('schools'):
                    all_schools.extend(data['schools'])
                
                if not data.get('links', {}).get('next'):
                    break
                    
                page += 1
                time.sleep(self.config.REQUEST_DELAY)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching data for ZIP {zip_code}: {str(e)}")
                break

        if not all_schools:
            logger.info(f"No schools found for ZIP code {zip_code}")
            return None

        return {'schools': all_schools}

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
        
        level_desc = f" for level(s) {self.config.LEVEL_CODES}" if self.config.LEVEL_CODES else ""
        logger.info(f"Starting collection for state {state}{level_desc} with {total_zips} ZIP codes")
        
        for i, zip_code in enumerate(zip_codes, 1):
            logger.info(f"Processing {state} ZIP {zip_code} ({i}/{total_zips})")
            
            response = self.fetch_schools_by_zip(zip_code, self.config.LEVEL_CODES)
            if response is not None:
                zip_school = pd.DataFrame(response['schools'])
                zip_school['zip'] = zip_code
                zip_school['state'] = state
                schools_df = pd.concat([schools_df, zip_school], ignore_index=True)
            
            time.sleep(self.config.REQUEST_DELAY)
        
        return schools_df

    def collect_all_states(self, level_codes: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Collect data for all configured states.
        
        Args:
            level_codes: Optional school level codes to filter by
            
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping state codes to their school data
        """
        state_data = {}
        
        level_desc = f"_{level_codes}" if level_codes else ""
        
        for state in self.config.STATES:
            logger.info(f"Starting collection for state: {state}")
            state_df = self.collect_state_data(state)
            
            # Save state data to CSV
            output_path = self.config.OUTPUT_DIR / f'schools_data_{state.lower()}{level_desc}.csv'
            state_df.to_csv(output_path, index=False)
            logger.info(f"Saved {state} data to {output_path}")
            
            state_data[state] = state_df
        
        # Create a combined dataset
        combined_df = pd.concat(state_data.values(), ignore_index=True)
        combined_path = self.config.OUTPUT_DIR / f'schools_data_all_states{level_desc}.csv'
        combined_df.to_csv(combined_path, index=False)
        logger.info(f"Saved combined data to {combined_path}")
        
        return state_data

def main():
    """Main execution function."""
    try:
        # Change current directory to the parent of the 'src' directory.
        current_dir = Path(__file__).resolve().parent
        os.chdir(current_dir.parent)

        # Initialize the collector and fetch data for all states
        config = Config()
        collector = SchoolDataCollector(config)
        state_data = collector.collect_all_states()  # Now collects all schools by default
        
        # Print summary statistics
        for state, df in state_data.items():
            logger.info(f"Collected {len(df)} schools for {state}")
            
    except Exception as e:
        logger.error(f"Script execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()