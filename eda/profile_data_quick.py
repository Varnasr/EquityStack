# Quick EDA report using pandas-profiling
import pandas as pd
from pandas_profiling import ProfileReport

def generate_profile(df):
    profile = ProfileReport(df, title="Data Profile Report", explorative=True)
    profile.to_file("profile_report.html")