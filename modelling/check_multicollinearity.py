"""Calculate VIFs to assess multicollinearity in predictors."""
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

def calculate_vif(df, features):
    X = df[features].assign(const=1)
    return pd.DataFrame({
        'variable': features,
        'vif': [variance_inflation_factor(X.values, i) for i in range(len(features))]
    })