# Ascending Project

This repository explores the relationship between school performance and intergenerational mobility in various U.S. commuting zones, leveraging data sources like school ratings and sentiment analysis of online reviews. The study aims to illuminate educational disparities and contribute to fostering equitable opportunities for upward social mobility.

## Table of Contents
- [Ascending Project](#ascending-project)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Research Questions](#research-questions)
  - [Data Sources](#data-sources)
  - [Methodology](#methodology)
  - [Data Cleaning and Wrangling](#data-cleaning-and-wrangling)
  - [Data Analysis and Visualization](#data-analysis-and-visualization)
  - [Project Structure](#project-structure)
  - [Contributors](#contributors)

## Introduction

This project investigates the interplay between school performance and intergenerational mobility within various commuting zones. By integrating school ratings and sentiment analysis of online reviews, it seeks to highlight patterns of educational disparities and propose avenues for promoting social mobility.

Originally focused solely on Illinois, the project has expanded to examine school performance across Wisconsin, Illinois, Indiana, and Michigan. This broader geographic scope enhances the generalizability of findings.

## Research Questions

1. How does school performance in Illinois commuting zones relate to intergenerational mobility within those zones?
2. Does higher school performance, as indicated by GreatSchools.org ratings, facilitate upward mobility across generations, or do structural barriers limit this relationship?

## Data Sources

The research utilizes the following datasets:

- **School Ratings:** Aggregated from GreatSchools.org to quantify school performance.
- **Official Education Data:** Includes graduation rates, test scores, and school demographic composition from state education departments.
- **Intergenerational Mobility Data:** Sourced from the [Equality of Opportunity Project](https://www.equality-of-opportunity.org), following the methodology of Alesina, Stantcheva, and Teso (2018).
- **Geospatial Data:** Includes school location mapping via **geopandas** and tract-to-commuting-zone conversions.

## Methodology

The study employs the following methods:

1. **Correlation Analysis:** Investigating associations between school performance and intergenerational mobility.
2. **Machine Learning Techniques:**
   - **Classification Model:** Categorizing school parameters based on their impact on intergenerational mobility.
   - **Regression Analysis:** Examining the influence of school characteristics (e.g., teacher-student ratio, student demographics) on mobility outcomes.
3. **Panel Data Analysis:** 
   - **Linear Regression:** Examining the impact of education-related variables on mobility outcomes.
   - **Random Forest Analysis:** Identifying the most influential factors affecting mobility.

## Data Cleaning and Wrangling

Datasets from different states contain redundancies and require standardization. Steps include:

- Merging education datasets with GreatSchools.org performance data.
- Standardizing school district, school name, and school type across multiple states.
- Mapping school locations to zip codes and aggregating data at the commuting zone level.

A **converter script** processes geographic data at the tract level, using **geopandas** to assign schools to respective tracts.

## Data Analysis and Visualization

The project applies:

- **Geographic heatmaps** to display intergenerational mobility rates and school performance.
- **Regression plots** to illustrate relationships between school quality and mobility.
- **Random forest feature importance graphs** to highlight key predictors of mobility.

Validation methods ensure that results generalize well, with residual diagnostics confirming robustness.

## Project Structure

The repository is organized as follows:
- `/data` 
  - `/edu` # Educational datasets (e.g., school performance data)
  - `/geo` # Geographic datasets (e.g., shapefiles, equivalency tables)
- `/notebooks` # Jupyter notebooks for exploratory and statistical analysis.
  - `converter.ipynb`
  - `great_schools_illinois.ipynb`
  - `regression.ipynb`
- `/src`
  - `collect_schools.py`
  - `converter.py`
  - `regression.py`
- `/results` # Generated outputs and visualizations.
- `Final Project Progress Report 1.pdf` # First project report.
- `README.md`
- `LICENSE`
- `requirements.txt` # Python dependencies required to run the project.
- `main.py` # Main entry point for orchestrating the project workflow.

## Contributors

- **Carrie Huang**
- **Jeanette Wu**
- **Kunjian Li**
- **Shirley Zhang**
