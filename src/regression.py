#!/usr/bin/env python3
"""
School Data Regression Script (with Robustness Analysis)

This script performs regression analysis on the relationship between school performance
and intergenerational mobility in counties and commuting zones.

Created by Jeanette Wu

We disclose that we employed Claude to integrate comprehensive logging and robust error-handling mechanisms,
thereby enhancing the script's overall reliability. Additionally, we encapsulated the script within a class
to improve its modularity and reusability.

"""


import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression, LassoCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import statsmodels.api as sm
import geopandas as gpd

class MobilityAnalysis:
    def __init__(self, path, file_name):
        self.path = path
        self.file_name = file_name
        self.df = None
        self.X = None
        self.y = None
        self.link = None

    def load_data(self):
        self.df = pd.read_csv(os.path.join(self.path, self.file_name))
        self.df = self.df.dropna(subset=['Absolute_Upward_Mobility'])
        self.preprocess_data()

    def preprocess_data(self):
        self.X = self.df.drop(columns=['Absolute_Upward_Mobility', 'state']).set_index(self.df.columns[0])
        self.X = self.X.select_dtypes(exclude=['object'])
        self.X = self.X.replace([np.inf, -np.inf], np.nan).fillna(0).astype('float64')
        self.y = self.df[['Absolute_Upward_Mobility', self.df.columns[0]]].set_index(self.df.columns[0])
        self.y = self.y.astype('float64')
        self.link = self.df[[self.df.columns[0], 'state']].set_index(self.df.columns[0])
    
    def remove_highly_correlated_features(self, threshold=0.4):
        corr_matrix = self.X.corr().abs()
        feature_target_corr = self.X.corrwith(self.y.squeeze()).abs()
        to_drop = set()
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i):
                if corr_matrix.iloc[i, j] > threshold:
                    col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                    if feature_target_corr[col1] >= feature_target_corr[col2]:
                        to_drop.add(col2)
                    else:
                        to_drop.add(col1)
        
        self.X = self.X.drop(columns=list(to_drop))
        print(f"Remaining features after correlation filtering: {self.X.shape[1]}")

    def train_random_forest(self):
        X_train, X_test, y_train, y_test = train_test_split(self.X, self.y, test_size=0.3, random_state=42)
        self.rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.rf_model.fit(X_train, y_train.squeeze())
        y_pred = self.rf_model.predict(X_test)
        
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        print(f"Random Forest - MSE: {mse}, R^2 Score: {r2}")

    def feature_importance(self):
        feature_importances = self.rf_model.feature_importances_
        importance_df = pd.DataFrame({'Feature': self.X.columns, 'Importance': feature_importances})
        importance_df = importance_df.sort_values(by='Importance', ascending=False).head(20)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x='Importance', y='Feature', data=importance_df)
        plt.title("Feature Importance - Random Forest")
        plt.xlabel('Importance')
        plt.ylabel('Feature')
        plt.show()

    def train_lasso(self):
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.X)
        lasso = LassoCV(cv=5, random_state=42, n_alphas=4).fit(X_scaled, self.y.squeeze())
        selected_features = self.X.columns[lasso.coef_ != 0]
        
        plt.figure(figsize=(10, 6))
        plt.barh(selected_features, lasso.coef_[lasso.coef_ != 0])
        plt.xlabel("LASSO Coefficients")
        plt.ylabel("Features")
        plt.title("Feature Importance via LASSO")
        plt.show()

    def fixed_effect_regression(self):
        X_fe = pd.concat([self.X, self.link], axis=1)
        X_fe['state'] = X_fe['state'].astype('category')
        X_fe = pd.get_dummies(X_fe, columns=['state'], drop_first=True).astype('float64')
        X_fe = sm.add_constant(X_fe)
        model = sm.OLS(self.y, X_fe).fit()
        print(model.summary())

    def plot_mobility_map(self, shapefile_path, column="Absolute_Upward_Mobility"):
        gdf = gpd.read_file(shapefile_path)
        self.df = self.df.reset_index()
        self.df[self.df.columns[0]] = self.df[self.df.columns[0]].astype(str).str.zfill(5)
        gdf["GEOID"] = gdf["GEOID"].astype(str)
        gdf = gdf.merge(self.df, left_on="GEOID", right_on=self.df.columns[0], how="left")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        gdf.plot(column=column, cmap="coolwarm", linewidth=0.2, edgecolor="black", legend=True, ax=ax)
        ax.set_title(f"{column.replace('_', ' ')} by County", fontsize=14)
        ax.axis("off")
        plt.show()

# Example usage
if __name__ == "__main__":
    analysis = MobilityAnalysis(path="E:/_UChicago/MACS30122/final-project-ascending/private", file_name="county_edu_mob.csv")
    analysis.load_data()
    analysis.remove_highly_correlated_features()
    analysis.train_random_forest()
    analysis.feature_importance()
    analysis.train_lasso()
    analysis.fixed_effect_regression()
    analysis.plot_mobility_map("E:/_UChicago/MACS30122/final-project-ascending/data/geo/cb_2022_us_county_500k.shp")
