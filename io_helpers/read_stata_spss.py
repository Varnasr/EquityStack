# Read STATA (.dta) and SPSS (.sav) files
import pyreadstat

def read_stata_file(filepath):
    df, meta = pyreadstat.read_dta(filepath)
    return df

def read_spss_file(filepath):
    df, meta = pyreadstat.read_sav(filepath)
    return df