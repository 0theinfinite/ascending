import csv
import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def scrape_reviews(url):
    """
    A simple requests + BeautifulSoup approach (no JS).
    If the site loads reviews via JavaScript, you may see only truncated or zero reviews.
    Adjust selectors as needed.
    """
    reviews = []
    try:
        response = requests.get(url)
        response.raise_for_status()  # raises an HTTPError for bad responses
    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return reviews

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Adjust the selector based on the actual HTML structure
    # For example, if each review is in <div class="review-item-container-threaded">
    review_elements = soup.find_all('div', class_='review-item-container-threaded')
    
    for element in review_elements:
        comment_div = element.find('div', class_='comment')
        if comment_div:
            review_text = comment_div.get_text(strip=True)
            reviews.append(review_text)
    
    return reviews

def analyze_sentiment_vader(review_text):
    """
    Returns a dictionary with VADER sentiment scores.
    """
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(review_text)
    return scores  # e.g. {'neg': 0.0, 'neu': 0.4, 'pos': 0.6, 'compound': 0.78}

def main():
    input_csv = '/Users/huangyiyang/Desktop/Winter_2025/MACS30122/final-project-ascending/data/greatschools/test_data.csv'      # The CSV with 'name' and 'overview-url'
    output_csv = '/Users/huangyiyang/Desktop/Winter_2025/MACS30122/final-project-ascending/data/greatschools/test_reviews.csv'

    with open(input_csv, newline='', encoding='utf-8') as f_in, \
         open(output_csv, 'w', newline='', encoding='utf-8') as f_out:
        
        reader = csv.DictReader(f_in)
        # We'll add some columns for sentiment scores
        fieldnames = ['name', 'overview-url', 'review_text', 'neg', 'neu', 'pos', 'compound']
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            school_name = row.get('name', '').strip()
            overview_url = row.get('overview-url', '').strip()
            
            # If the GreatSchools URL doesn't end with /reviews/, append it
            if not overview_url.endswith('/reviews/'):
                overview_url = overview_url.rstrip('/') + '/reviews/'
            
            # 1) Scrape reviews
            reviews = scrape_reviews(overview_url)
            
            # 2) If no reviews, write a row with empty review field
            if not reviews:
                writer.writerow({
                    'name': school_name,
                    'overview-url': overview_url,
                    'review_text': '',
                    'neg': '',
                    'neu': '',
                    'pos': '',
                    'compound': ''
                })
                print(f"No reviews found for {school_name}")
            else:
                # 3) Analyze each review with VADER
                for r in reviews:
                    scores = analyze_sentiment_vader(r)
                    writer.writerow({
                        'name': school_name,
                        'overview-url': overview_url,
                        'review_text': r,
                        'neg': scores['neg'],
                        'neu': scores['neu'],
                        'pos': scores['pos'],
                        'compound': scores['compound']
                    })
            print(f"Scraped and analyzed {len(reviews)} reviews for {school_name}")

if __name__ == '__main__':
    main()
