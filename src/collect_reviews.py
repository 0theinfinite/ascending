import csv
import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
import time
import os
import logging
from datetime import datetime


class SchoolReviewsScraper:
    """A class for scraping and analyzing school reviews from GreatSchools."""
    
    def __init__(self, log_level=logging.INFO, log_frequency='minimal'):
        """
        Initialize the scraper with configurable logging.
        
        Args:
            log_level: Logging level (default: logging.INFO)
            log_frequency: 'minimal' or 'detailed' logging (default: 'minimal')
        """
        self.log_frequency = log_frequency
        
        # Configure logging
        log_filename = f'scraper_{datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"SchoolReviewsScraper initialized with {log_frequency} logging")
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    def scrape_reviews(self, url):
        """
        Scrape reviews from the JSON-LD <script> tag on a GreatSchools page.
        
        Args:
            url: The URL of the school reviews page
            
        Returns:
            List of review texts or None if scraping failed
        """
        if self.log_frequency == 'detailed':
            self.logger.info(f"Scraping reviews from: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Error accessing {url}: {e}")
            return None

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', attrs={'type': 'application/ld+json'})
            
            if not script_tag:
                self.logger.warning(f"No JSON-LD script tag found at {url}")
                return None

            data = json.loads(script_tag.string)
            reviews_list = data.get('review', [])
            
            all_reviews = []
            for review_obj in reviews_list:
                review_text = review_obj.get('reviewBody', '').strip()
                if review_text:
                    all_reviews.append(review_text)
            
            if self.log_frequency == 'detailed':
                self.logger.info(f"Found {len(all_reviews)} reviews")
            return all_reviews

        except Exception as e:
            self.logger.error(f"Error parsing page content: {e}")
            return None

    def analyze_sentiment(self, review_text):
        """
        Returns a dictionary with VADER sentiment scores.
        
        Args:
            review_text: Single review text or list of reviews
            
        Returns:
            Dictionary containing sentiment scores
        """
        try:
            if isinstance(review_text, list):
                combined_text = " ".join(review_text)
                scores = self.sentiment_analyzer.polarity_scores(combined_text)
            else:
                scores = self.sentiment_analyzer.polarity_scores(review_text)
                
            return scores
            
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {e}")
            return {'neg': 0.0, 'neu': 0.0, 'pos': 0.0, 'compound': 0.0}
    
    def process_schools_csv(self, input_path, output_path, delay=0.1):
        """
        Process a CSV file of schools, scrape their reviews, and save results.
        
        Args:
            input_path: Path to the input CSV file
            output_path: Path to save the output CSV file
            delay: Delay between requests in seconds (default: 0.1)
            
        Returns:
            Number of schools processed successfully
        """
        self.logger.info(f"Starting to process schools from {input_path}")
        successful_count = 0
        
        try:
            with open(input_path, newline='', encoding='utf-8') as f_in, \
                 open(output_path, 'w', newline='', encoding='utf-8') as f_out:
                
                reader = csv.DictReader(f_in)
                writer = csv.DictWriter(f_out, fieldnames=['universal_id', 'overview-url', 'state', 'reviews', 'sentiment_scores'])
                writer.writeheader()
                
                total_schools = sum(1 for _ in reader)
                f_in.seek(0)
                next(reader)  # Skip header
                
                for idx, row in enumerate(reader, 1):
                    try:
                        universal_id = row.get('universal-id', '')
                        overview_url = row.get('overview-url', '').strip()
                        state = row.get('state', '').strip()
                        
                        # Log progress at intervals
                        if idx % 10 == 0 or idx == 1 or idx == total_schools:
                            self.logger.info(f"Processing school {idx}/{total_schools} - ID: {universal_id}")
                        
                        # Ensure URL ends with /reviews/
                        if not overview_url.endswith('/reviews/'):
                            overview_url = overview_url.rstrip('/') + '/reviews/'
                        
                        # Scrape and analyze
                        reviews = self.scrape_reviews(overview_url)
                        
                        if not reviews:
                            writer.writerow({
                                'universal_id': universal_id,
                                'overview-url': overview_url,
                                'state': state,
                                'reviews': [],
                                'sentiment_scores': None
                            })
                            if self.log_frequency == 'detailed':
                                self.logger.warning(f"No reviews found for ID: {universal_id}")
                        else:
                            scores = self.analyze_sentiment(reviews)
                            writer.writerow({
                                'universal_id': universal_id,
                                'overview-url': overview_url,
                                'state': state,
                                'reviews': reviews,
                                'sentiment_scores': scores
                            })
                            successful_count += 1
                            
                            if self.log_frequency == 'detailed':
                                self.logger.info(f"Processed {len(reviews)} reviews for ID: {universal_id}")
                        
                    except Exception as e:
                        self.logger.error(f"Error processing {universal_id}: {e}")
                        continue
                    
                    # Polite delay between requests
                    time.sleep(delay)
                    
            self.logger.info(f"Scraping completed: {successful_count} schools processed successfully")
            return successful_count
                    
        except FileNotFoundError as e:
            self.logger.error(f"File not found: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise


def main():
    """Example usage of the SchoolReviewsScraper class"""
    try:
        # Change to parent directory if needed
        os.chdir(os.path.dirname(os.getcwd()))
        
        # Define file paths
        input_csv = '/Users/huangyiyang/Desktop/Winter_2025/MACS30122/final-project-ascending/data/greatschools/schools_data_all_states.csv'
        output_csv = '/Users/huangyiyang/Desktop/Winter_2025/MACS30122/final-project-ascending/data/greatschools/review_data_all_states.csv'
        
        # Initialize and run the scraper
        scraper = SchoolReviewsScraper(log_frequency='minimal')
        scraper.process_schools_csv(input_csv, output_csv)
        
    except Exception as e:
        logging.error(f"Main execution error: {e}")
        raise


if __name__ == '__main__':
    main()