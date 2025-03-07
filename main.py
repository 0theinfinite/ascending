"""
main.py

Main script for the ascending_macs project, analyzing the relationship between school performance
and intergenerational mobility in Illinois commuting zones.

Author: Carrie Huang, Jeanette Wu, Kunjian Li, Shirley Zhang
"""

import os
import argparse
from src.collect_reviews import *
from src.collect_schools import *
from src.converter import *
from src.visualization import *
from src.sentiment_analysis import *


current_dir = os.path.dirname(os.path.realpath(__file__))
path_to_map = os.path.join(current_dir, "data", "il_map.geojson")


if __name__ == "__main__":
    print("Welcome to the Ascending MACS project!")