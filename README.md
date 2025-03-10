# Ascending Project
## Project Goals
This repository explores the relationship between school profile characteristics and intergenerational mobility in various counties and commuting zones at states, leveraging data sources like school statistics and sentiment analysis of online reviews, controlling economic and geographic indicators. 

## Table of Contents
- [Ascending Project](#ascending-project)
  - [Project Goals](#project-goals)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
    - [Research Questions](#research-questions)
    - [Overall Findings](#overall-findings)
  - [Data Sources](#data-sources)
  - [Libraries](#libraries)
  - [Project Structure](#project-structure)
  - [Contributors](#contributors)

## Introduction

This project investigates the interplay between school performance and intergenerational mobility within various counties and commuting zones. By integrating school ratings and sentiment analysis of online reviews into the **county** and **commuting zone** levels, it seeks to highlight patterns of educational disparities and propose avenues for promoting social mobility.

Originally focused solely on Illinois, the project has expanded to examine school performance across Wisconsin, Illinois, Indiana, and Michigan. This broader geographic scope enhances the generalizability of findings.

Education lies at the core of social mobility, shaping opportunities and outcomes for future generations. By examining key factors such as race/ethnicity, household income, school resources, this project highlights the systemic inequalities that can affect students’ social mobility. Understanding how these variables interact allows us to pinpoint where disparities arise and to inform policies aimed at promoting equitable resource distribution. The study aims to illuminate educational disparities and contribute to fostering equitable opportunities for upward social mobility.

You are welcome to watch our introduction video accessible at: https://uchicago.box.com/s/i2nnfenbymhwqhh9eo9gtv417a6ttz8x

### Research Questions

Which factors/characteristics of school profile contribute to the prediction of intergenerational mobility?

### Overall Findings
- Notably, a higher proportion of Black students and students from low-income families are associated with lower mobility.
- Negative ratings and accessbility of educaitonal resources play a crucial role. This finding aligns with broader research on systemic barriers to economic mobility faced by marginalized groups. 
- Our project indicates that race is a predominant determinant of intergenerational mobility, followed by the influence of income and educational resources. This effect remains robust across both county-level and commuting zone-level analyses, cross validated by machine learning algorithms. 


## Data Sources

The research utilizes the following datasets:

- **School Statistics:** Scraped and aggregated from GreatSchools.org to quantify school performance, utilizing the GreatSchools.org API. These data are crosschecked with Government data for authenticity. School profile characteristics including college preparation, advanced courses, test scores, students ethnicity, low-income family proportions and so on. 
- **School Reviews:** Scraped school reviews from the review section of school's introduction website, as the ingredients for sentiment analysis.
- **Intergenerational Mobility Data:** Sourced from the Chetty et al.’s dataset (2014), from their paper “[Where is the land of Opportunity? The Geography of Intergenerational Mobility in the United States](https://academic.oup.com/qje/article-abstract/129/4/1553/1853754)”.
- **Geospatial Data:** School locations in geographic coordinates, mapped to high levels via **geopandas**, i.e. the tract-to-county and -to-commuting-zone conversions. This also include county shapes, zip codes and so on.
- **Census Data**: Regional demographic records, accessible at census.gov, including average income per capita, population (growth), land acres and so on.

## Libraries
See `requirements.txt`.


## Project Structure

The repository is organized as follows:
- `/data`: data folder: 
  - `/edu`: Educational datasets (e.g., government school performance data), but we are only consulting it for research insights and do not use it in the code. 
  - `/geo`: Geographic datasets (e.g., shapefiles, equivalency tables).
  - `/greatschools`: Contains all scraped data from GreatSchools (e.g., school descriptive data, ratings, comments and reviews).
  - `/links`: Datasets to link schools to higher levels through it coordinates, and county/commuting zone identifiers.
  - `intergenerational_mobility.xls`: Excel file Chetty et al. (2014). Sheet 3,5 and 8 are utilized.
- `/src`:
  - `collect_schools.py`: Scrape GreatSchools API data.
  - `collect_reviews.py`: Scrape the review sections from GreatSchools and perform Vader Sentiment analysis.
  - `quantity_scraper.py`: Scrape the ratings and statistics of schools. 
  - `converter.py`: Link our 4-layered-geographic-hierachy (school, tract, county, and commuting zone)
  - `merge_data.py`: Merge different data sets, aggregate school-level data to county-level and commuting-zone-level, and match with respective intergenerational mobility data. 
  - `regression.py`: Perform dimensionality reduction, casual inference, machine learning, visualizations, and performance evaluation.
- `requirements.txt` # Python dependencies required to run the project.
- `main.py` # Main entry point for orchestrating the project workflow.
- `Progress_Report_1.pdf` and `Progress_Report_2.pdf`
- `Ascending-Slides_Final_Presentation.pdf` and `Ascending-Slides_Final_Presentation-UPDATED.pdf`
- `/results`
- `README.md`
- `LICENSE`

## Contributors
- **Kunjian Li**: Project management. GreatSchools API maintenance. Collected school descriptive and quantitative rating data from GreatSchools. GitHub repository management. Draft presentation slides. 
- **Jeanette Wu**: Collected reviews from GreatSchools. Data exploration, dimensionality reduction (correlation matrix and LASSO), regression (Random Forest, OLS, and fixed effects), and visualizations. 
- **Shirley Zhang**: Collected geographic data. Built a converter to manipulate data on different hierarchical levels. Scraped school quantitative rating data from GreatSchools. Draft presentation slides. 
- **Carrie Huang**: Collected and processed reviews from GreatSchools, and performed sentiment analysis. Merged and prepare data for data analysis. Aggregate school-level data to county and commuting zone levels. Draft README and project updates.

