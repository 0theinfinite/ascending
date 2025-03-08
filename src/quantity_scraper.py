#!/usr/bin/env python3
"""
School Statistics Collection Script

This script fetches school statistics looping the urls provided by the GreatSchools API and cleans the data.

Created by Shirley Zhang, Kunjian Li

We disclose that we employed Claude to integrate comprehensive logging and robust error-handling mechanisms,
thereby enhancing the script's overall reliability. Additionally, we encapsulated the script within a class
to improve its modularity and reusability.

"""


import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import logging
from fake_useragent import UserAgent
import random
import re

class CONFIG:
    # File paths
    INPUT_FILE = 'data/greatschools/schools_data_all_states.csv'
    OUTPUT_FILE = 'data/greatschools/scraped_ratings.csv'
    
    # Logging configuration
    LOG_FORMAT = '%(asctime)s - %(message)s'
    LOG_FILE = 'scraper.log'
    LOG_LEVEL = logging.INFO
    
    # Request configuration
    REQUEST_TIMEOUT = 10
    REQUEST_DELAY = 0.1  # seconds between requests
    
    # Default User Agents
    DEFAULT_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/91.0.4472.124',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Firefox/89.0'
    ]
    
    # Request headers
    DEFAULT_HEADERS = {
        'From': 'kunjianli@uchicago.edu',
        'Comment': 'Data collection for research purposes at University of Chicago'
    }
    
    # Batch processing
    SAVE_BATCH_SIZE = 100

class SchoolScraper:
    def __init__(self, input_file=None, output_file=None):
        # Initialize logging
        logging.basicConfig(
            level=CONFIG.LOG_LEVEL,
            format=CONFIG.LOG_FORMAT,
            handlers=[
                logging.FileHandler(CONFIG.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        
        self.input_file = input_file or CONFIG.INPUT_FILE
        self.output_file = output_file or CONFIG.OUTPUT_FILE
        try:
            self.ua = UserAgent()
        except:
            self.ua = None
            logging.warning("Could not initialize UserAgent, using fallback")

    def get_random_headers(self):
        """Get headers with random user agent"""
        user_agent = self.ua.random if self.ua else random.choice(CONFIG.DEFAULT_USER_AGENTS)
        headers = CONFIG.DEFAULT_HEADERS.copy()
        headers['User-Agent'] = user_agent
        return headers

    def school_improvement(self, block):
        """Extract school improvement data."""
        try:
            improvements = block.find('script', class_='js-react-on-rails-component')
            improvements = improvements.text if improvements else None
            if not improvements:
                return None
            
            improvements = json.loads(improvements)['data']
            imp_dict = {}
            
            for improvement in improvements:
                category = improvement.get('name', None)
                if category:
                    score = improvement.get('school_value', 0)
                    imp_dict[category] = score
            return imp_dict
        except Exception as e:
            logging.error(f"Error in school_improvement: {e}")
            return None

    def college_prep(self, block):
        """Extract college preparation statistics."""
        try:
            script_tag = block.find('script', {'class': 'js-react-on-rails-component'})
            if not script_tag:
                return None

            json_data = json.loads(script_tag.string)
            if 'data' not in json_data:
                return None

            college_prep_dict = {}
            for item in json_data['data']:
                metric_name = item['breakdown']
                school_value = item['value']
                state_value = item['state_value']
                
                if 'value_label' in item:
                    school_value = item['value_label']
                    state_value = item.get('state_value_label')
                
                college_prep_dict[metric_name] = {
                    'school_value': school_value,
                    'state_value': state_value
                }
            return college_prep_dict
        except Exception as e:
            logging.error(f"Error in college_prep: {e}")
            return None

    def college_success(self, block):
        """Extract college success metrics."""
        try:
            script_tag = block.find('script', {'class': 'js-react-on-rails-component'})
            if not script_tag:
                return None

            data = json.loads(script_tag.string)
            if 'data' not in data:
                return None

            college_success_dict = {}
            for item in data['data']:
                metric_name = item['breakdown']
                college_success_dict[metric_name] = {
                    'school_value': f"{item['value']}%",
                    'state_value': f"{item['state_value']}%"
                }
            return college_success_dict
        except Exception as e:
            logging.error(f"Error in college_success: {e}")
            return None

    def advanced_courses(self, block):
        """Extract advanced courses metrics."""
        try:
            script_tag = block.find('script', {'class': 'js-react-on-rails-component'})
            if not script_tag:
                return None

            data = json.loads(script_tag.string)
            if 'data' not in data:
                return None

            advanced_courses_dict = {}
            for item in data['data']:
                advanced_courses_dict[item['breakdown']] = {
                    'school_value': f"{item['value']}%",
                    'state_value': f"{item['state_value']}%"
                }
            return advanced_courses_dict
        except Exception as e:
            logging.error(f"Error in advanced_courses: {e}")
            return None

    def test_scores(self, block):
        """Extract test scores data."""
        try:
            script_tag = block.find('script', {'class': 'js-react-on-rails-component'})
            if not script_tag:
                return None

            data = json.loads(script_tag.string)
            if 'data' not in data:
                return None

            scores = {}
            for item in data['data']:
                subject = item['breakdown']
                scores[subject] = {
                    'overall': {
                        'school_value': item['value'],
                        'state_value': item['state_value']
                    },
                    'by_grade': {}
                }
                
                if 'sub_rows' in item:
                    for grade_data in item['sub_rows']:
                        grade = grade_data['breakdown']
                        scores[subject]['by_grade'][grade] = {
                            'school_value': grade_data['value'],
                            'state_value': grade_data['state_value']
                        }
            return scores
        except Exception as e:
            logging.error(f"Error in test_scores: {e}")
            return None

    def teacher_staff(self, block):
        """Extract teacher and staff data."""
        try:
            staffs = block.find('script', class_='js-react-on-rails-component')
            staffs = staffs.text if staffs else None
            if not staffs:
                return None

            # First check if data exists
            if 'data' not in json.loads(staffs):
                return None

            # Then parse the data
            staffs = json.loads(staffs)['data']
            stf_dict = {}

            for staff in staffs:
                category = staff.get('label', None)
                if category:
                    score_school = staff.get('score', None)
                    score_state = staff.get('state_average', None)

                    if isinstance(score_school, dict):
                        score_school = score_school.get('value', 0)
                    if isinstance(score_state, dict):
                        score_state = score_state.get('value', 0)
                    
                    stf_dict[category] = {'school': score_school, 'state': score_state}
            return stf_dict
        except Exception as e:
            logging.error(f"Error in teacher_staff: {e}")
            return None

    def courses_programs(self, block):
        """Extract courses and programs data."""
        try:
            script_tags = block.find_all('script', {'class': 'js-react-on-rails-component'})
            courses_programs_dict = {}
            
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    
                    if 'content' in data:
                        content = data['content']
                        if '(' in content:
                            category = content.split('(')[0].strip()
                            number = int(content.split('(')[1].replace(')', ''))
                            courses_programs_dict[category] = number
                            
                    if 'courseNumber' in data:
                        courses_programs_dict['Total Courses'] = data['courseNumber']
                except json.JSONDecodeError:
                    continue
                    
            return courses_programs_dict
        except Exception as e:
            logging.error(f"Error in courses_programs: {e}")
            return None

    def student_demographics(self, block):
        """Extract student demographics data."""
        try:
            demographics = block.find('script', class_='js-react-on-rails-component')
            demographics = demographics.text if demographics else None
            if not demographics:
                return None
            
            # Parse the JSON data
            demographics = json.loads(demographics)['data']
            dem_dict = {}
            
            for demographic in demographics.keys():
                if demographic == 'ethnicity_data':
                    eth_dict = {}
                    for eth in demographics[demographic]:
                        eth_name = eth.get('breakdown', None)
                        if eth_name:
                            eth_value = eth.get('value', 0)  # for robustness
                            eth_dict[eth_name] = eth_value
                    if eth_dict:
                        dem_dict['ethnicity'] = eth_dict
                
                if demographic == 'gender_data':
                    gender_dict = {}
                    genders = demographics[demographic].get('value', None)
                    if genders:
                        for gender in genders:
                            gender_name = gender.get('breakdown', None)
                            if gender_name:
                                gender_value = gender.get('school_value', 0)  # for robustness
                                gender_dict[gender_name] = gender_value
                    if gender_dict:
                        dem_dict['gender'] = gender_dict
                
                if demographic == 'subgroups_data':
                    subgroup_dict = {}
                    subgroups = demographics[demographic].get('value', None)
                    if subgroups:
                        for subgroup in subgroups:
                            subgroup_name = subgroup.get('breakdown', None)
                            if subgroup_name:
                                subgroup_value = subgroup.get('school_value', 0)
                                subgroup_dict[subgroup_name] = subgroup_value
                    if subgroup_dict:
                        dem_dict['subgroups'] = subgroup_dict
            
            return dem_dict
        except Exception as e:
            logging.error(f"Error in student_demographics: {e}")
            return None


    def scrape_school(self, url, school_id):
        """Scrape data for a single school"""
        try:
            response = requests.get(url, headers=self.get_random_headers(), timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            school_data = {}
            
            for block in soup.find_all('div', class_='gs-v2'):
                title_elem = block.find('h2', class_='title-text')
                if not title_elem:
                    continue
                    
                module_title = title_elem.text.strip()
                
                # Process based on module type
                if 'School Improvement' in module_title:
                    result = self.school_improvement(block)
                    if result:
                        school_data['school_improvement'] = result
                        
                elif 'College Prep' in module_title:
                    result = self.college_prep(block)
                    if result:
                        school_data['college_prep'] = result
                        
                elif 'College Success' in module_title:
                    result = self.college_success(block)
                    if result:
                        school_data['college_success'] = result
                        
                elif 'Advanced Courses' in module_title:
                    result = self.advanced_courses(block)
                    if result:
                        school_data['advanced_courses'] = result
                        
                elif 'Test Scores' in module_title:
                    result = self.test_scores(block)
                    if result:
                        school_data['test_scores'] = result
                        
                elif 'Courses & Programs' in module_title:
                    result = self.courses_programs(block)
                    if result:
                        school_data['courses_programs'] = result
                        
                elif 'Teachers & Staff' in module_title:
                    result = self.teacher_staff(block)
                    if result:
                        school_data['teachers_staff'] = result

                elif 'Student Demographics' in module_title:
                    result = self.student_demographics(block)
                    if result:
                        school_data['student_demographics'] = result

            time.sleep(0.1)  # Be nice to the server
            return {school_id: school_data}

        except Exception as e:
            logging.error(f"Error scraping school {school_id}: {str(e)}")
            return {school_id: {}}


    @staticmethod
    def parse_scraped_data(json_data):
        """
        Static method to parse scraped JSON data into a flattened DataFrame.
        
        Parameters:
            json_data (dict): Dictionary containing scraped school data
            
        Returns:
            pd.DataFrame: A DataFrame with one row per school and flattened columns
        """
        rows = []

        # Each key in the JSON is a school id
        for school_id, school_data in json_data.items():
            # Initialize row with the school identifier
            row = {'school_id': school_id}
            if not school_data:
                rows.append(row)
                continue
            
            # Process School Improvement
            if 'school_improvement' in school_data and school_data['school_improvement']:
                for category, score in school_data['school_improvement'].items():
                    col_name = f"school_improvement_{category}"
                    row[col_name] = score
            
            # Process College Prep
            if 'college_prep' in school_data and school_data['college_prep']:
                for metric, values in school_data['college_prep'].items():
                    row[f"college_prep_{metric}_school_value"] = values.get('school_value')
                    row[f"college_prep_{metric}_state_value"] = values.get('state_value')
            
            # Process College Success
            if 'college_success' in school_data and school_data['college_success']:
                for metric, values in school_data['college_success'].items():
                    row[f"college_success_{metric}_school_value"] = values.get('school_value')
                    row[f"college_success_{metric}_state_value"] = values.get('state_value')
            
            # Process Advanced Courses
            if 'advanced_courses' in school_data and school_data['advanced_courses']:
                for metric, values in school_data['advanced_courses'].items():
                    row[f"advanced_courses_{metric}_school_value"] = values.get('school_value')
                    row[f"advanced_courses_{metric}_state_value"] = values.get('state_value')
            
            # Process Test Scores
            if 'test_scores' in school_data and school_data['test_scores']:
                for subject, subject_data in school_data['test_scores'].items():
                    overall = subject_data.get('overall', {})
                    row[f"test_scores_{subject}_overall_school_value"] = overall.get('school_value')
                    row[f"test_scores_{subject}_overall_state_value"] = overall.get('state_value')
                    
                    by_grade = subject_data.get('by_grade', {})
                    for grade, grade_data in by_grade.items():
                        row[f"test_scores_{subject}_{grade}_school_value"] = grade_data.get('school_value')
                        row[f"test_scores_{subject}_{grade}_state_value"] = grade_data.get('state_value')
            
            # Process Teachers & Staff
            if 'teachers_staff' in school_data and school_data['teachers_staff']:
                for category, values in school_data['teachers_staff'].items():
                    row[f"teachers_staff_{category}_school"] = values.get('school')
                    row[f"teachers_staff_{category}_state"] = values.get('state')
            
            # Process Courses & Programs
            if 'courses_programs' in school_data and school_data['courses_programs']:
                for category, number in school_data['courses_programs'].items():
                    row[f"courses_programs_{category}"] = number

            # Process Student Demographics
            if 'student_demographics' in school_data and school_data['student_demographics']:
                demographics = school_data['student_demographics']
                
                if 'ethnicity' in demographics:
                    for ethnicity, value in demographics['ethnicity'].items():
                        row[f"demographics_ethnicity_{ethnicity}"] = value
                
                if 'gender' in demographics:
                    for gender, value in demographics['gender'].items():
                        row[f"demographics_gender_{gender}"] = value
                
                if 'subgroups' in demographics:
                    for subgroup, value in demographics['subgroups'].items():
                        row[f"demographics_subgroup_{subgroup}"] = value

            rows.append(row)
        
        return pd.DataFrame(rows)

    def run(self):
        """Run the scraper"""
        try:
            df = pd.read_csv(self.input_file)
            urls = df[['universal-id', 'overview-url']].dropna()
            
            logging.info(f"Starting to scrape {len(urls)} schools")
            all_data = {}
            
            for i, row in urls.iterrows():
                logging.info(f"Processing school {i+1}/{len(urls)}: {row['universal-id']}")
                result = self.scrape_school(row['overview-url'], row['universal-id'])
                all_data.update(result)
                
                if (i + 1) % CONFIG.SAVE_BATCH_SIZE == 0:
                    with open(self.output_file, 'w') as f:
                        json.dump(all_data, f)
                    logging.info(f"Saved progress: {i+1} schools processed")
            
            # Parse the scraped data and save as CSV
            df = self.parse_scraped_data(all_data)
            df.to_csv(self.output_file, index=False)
            
            logging.info("Scraping completed successfully")
            
        except Exception as e:
            logging.error(f"Fatal error: {str(e)}")
            raise

if __name__ == "__main__":
    scraper = SchoolScraper()
    scraper.run()