# Group name: Ascending  
# Group members: Jeanette, Kunjian, Shirley, Carrie

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LassoCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import statsmodels.api as sm
import geopandas as gpd
from sklearn.preprocessing import StandardScaler

# File Path
dataset_path = r'E:\_UChicago\MACS30122\final-project-ascending\private'
shapefile_county = r"E:\_UChicago\MACS30122\final-project-ascending\data\geo\cb_2022_us_county_500k.shp"

# Load Data
df_county = pd.read_csv(os.path.join(dataset_path, 'county_edu_mob.csv'))
df_county = df_county.dropna(subset=['Absolute_Upward_Mobility'])

df_cz = pd.read_csv(os.path.join(dataset_path, 'cz_from_county_edu_mob.csv'))
df_cz = df_cz.dropna(subset=['Absolute_Upward_Mobility'])
df_cz.head()

# Data Preprocessing
X = df_county.drop(columns=['Absolute_Upward_Mobility', 'CZ_ID', 'state']).set_index('County_FIPS')
X = X.select_dtypes(exclude=['object']).replace([np.inf, -np.inf], np.nan).fillna(0).astype('float64')
y = df_county[['Absolute_Upward_Mobility', 'County_FIPS']].set_index('County_FIPS')
link = df_county[['County_FIPS', 'state']].set_index('County_FIPS')

X = df_cz.drop(columns=['Absolute_Upward_Mobility', 'state']).set_index('CZ_ID')
X = X.select_dtypes(exclude=['object']).replace([np.inf, -np.inf], np.nan).fillna(0).astype('float64')
y = df_cz[['Absolute_Upward_Mobility', 'CZ_ID']].set_index('CZ_ID')
y = y.astype('float64')
link = df_cz[['CZ_ID', 'state']].set_index('CZ_ID')

columns_to_keep = ['demographics_ethnicity_Black',
 'demographics_gender_Male',
 'demographics_subgroup_Students from low-income families',
 'teachers_staff_Students per teacher_state',
 'teachers_staff_Students per counselor_school',
 'courses_programs_Academic programs',
 'courses_programs_Art courses',
 'college_prep_SAT participation rate_school_value',
 'neg',
 'state_IN',
 'state_MI',
 'state_WI']

X_fe = pd.concat([X, link], axis=1)
X_fe['state'] = X_fe['state'].astype('category')
X_fe = pd.get_dummies(X_fe, columns=['state'], drop_first=True).astype('float64')
X_fe = X_fe[columns_to_keep]
X_fe = sm.add_constant(X_fe)
model_fe = sm.OLS(y, X_fe).fit()
print(model_fe.summary())

def remove_highly_correlated_features(X: pd.DataFrame, y: pd.Series, threshold: float):
    corr_matrix = X.corr().abs()
    feature_target_corr = X.corrwith(y).abs()
    to_drop = set()
    for i in range(len(corr_matrix.columns)):
        for j in range(i):
            if corr_matrix.iloc[i, j] > threshold:
                col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                to_drop.add(col2 if feature_target_corr[col1] >= feature_target_corr[col2] else col1)
    return list(to_drop)

to_drop = remove_highly_correlated_features(X, y, 0.4)
X_selected = X.drop(columns=list(to_drop))

# Random Forest Regression
y_rf = pd.concat([y, link], axis=1)
y_rf['state_mean'] = y_rf.groupby('state')['Absolute_Upward_Mobility'].transform('mean')
y_rf['Relative_Upward_Mobility'] = y_rf['Absolute_Upward_Mobility'] - y_rf['state_mean']
y_rf = y_rf.drop(columns=['Absolute_Upward_Mobility', 'state_mean', 'state'])

X_train, X_test, y_train, y_test = train_test_split(X_selected, y_rf, test_size=0.3, random_state=42)
rf_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
rf_regressor.fit(X_train, y_train)
y_pred = rf_regressor.predict(X_test)
print(f"Mean Squared Error: {mean_squared_error(y_test, y_pred)}")
print(f"R^2 Score: {r2_score(y_test, y_pred)}")

# Feature Importance Plot
importance_df = pd.DataFrame({'Feature': X_selected.columns, 'Importance': rf_regressor.feature_importances_})
importance_df = importance_df.sort_values(by='Importance', ascending=False).head(20)
plt.figure(figsize=(10, 6))
sns.barplot(x='Importance', y='Feature', data=importance_df, palette='viridis')
plt.title("Top 20 Feature Importance - Random Forest Regressor", fontsize=14, fontweight='bold')
plt.xlabel('Importance')
plt.ylabel('Feature')
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.show()
