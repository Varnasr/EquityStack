# Quick EDA report using ydata-profiling.
#
# This was pandas-profiling, which the maintainers renamed to ydata-profiling at
# version 4. The import path changed with it: pandas_profiling no longer exists,
# and the old package fails to install on Python 3.11 because its htmlmin
# dependency cannot build a wheel.
import pandas as pd
from ydata_profiling import ProfileReport

def generate_profile(df):
    profile = ProfileReport(df, title="Data Profile Report", explorative=True)
    profile.to_file("profile_report.html")