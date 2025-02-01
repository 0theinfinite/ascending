import pandas as pd
import numpy as np
import statsmodels.api as sm
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import norm
from sklearn.tree import DecisionTreeRegressor

class MobilityAnalyzer:
    def __init__(self, df):
        self.df = df
        self.scaler = StandardScaler()
        
    def prepare_data(self):
        """Prepare and standardize data for analysis"""
        education_cols = [
            "Intergen_Mobility", 
            "High_School_Grad_Rate", "College_Graduation_Rate", "Teacher_Student_Ratio",
            "Dropout_Rate", "College_Entrance_Rate", "Public_School_Ranking"
        ]
        
        self.df_education = self.df[education_cols].copy()
        self.df_education.iloc[:, 1:] = self.scaler.fit_transform(self.df_education.iloc[:, 1:])
        return self.df_education
    
    def run_ols_regression(self, X, y):
        """Run OLS regression with detailed diagnostics"""
        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()
        
        # Add heteroskedasticity tests
        het_white = sm.stats.diagnostic.het_white(model.resid, model.model.exog)
        het_bp = sm.stats.diagnostic.het_breuschpagan(model.resid, model.model.exog)
        
        return {
            'model': model,
            'white_test': het_white,
            'bp_test': het_bp
        }
    
    def plot_education_relationships(self):
        """Create enhanced visualization of education relationships"""
        fig = plt.figure(figsize=(15, 10))
        
        education_vars = [col for col in self.df_education.columns if col != "Intergen_Mobility"]
        
        for idx, var in enumerate(education_vars, 1):
            ax = fig.add_subplot(2, 3, idx)
            
            # Add regression plot with confidence intervals
            sns.regplot(
                x=var,
                y="Intergen_Mobility",
                data=self.df_education,
                scatter_kws={'alpha':0.5, 's':20},
                line_kws={'color':'red'},
                ci=95
            )
            
            # Add correlation coefficient
            corr = self.df_education[var].corr(self.df_education["Intergen_Mobility"])
            plt.annotate(f'r = {corr:.2f}', xy=(0.05, 0.95), xycoords='axes fraction')
            
            plt.title(f"{var.replace('_', ' ')} vs Mobility")
            
        plt.tight_layout()
        return fig
    
    def run_random_forest(self):
        """Enhanced Random Forest analysis with feature importance visualization"""
        X = self.df.drop("Intergen_Mobility", axis=1)
        y = self.df["Intergen_Mobility"]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        rf = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        
        rf.fit(X_train, y_train)
        
        # Calculate feature importances with standard deviation
        importances = rf.feature_importances_
        std = np.std([tree.feature_importances_ for tree in rf.estimators_], axis=0)
        
        # Plot feature importances with error bars
        indices = np.argsort(importances)[::-1]
        
        plt.figure(figsize=(12, 6))
        plt.title("Feature Importances with Standard Deviation")
        plt.bar(range(X.shape[1]), importances[indices],
                yerr=std[indices], align="center")
        plt.xticks(range(X.shape[1]), X.columns[indices], rotation=45, ha='right')
        plt.tight_layout()
        
        return {
            'model': rf,
            'importance_indices': indices,
            'importance_values': importances,
            'test_score': rf.score(X_test, y_test)
        }
    
    def plot_residual_analysis(self):
        """Enhanced residual analysis with multiple diagnostic plots"""
        X = self.df_education.drop("Intergen_Mobility", axis=1)
        y = self.df_education["Intergen_Mobility"]
        
        model = self.run_ols_regression(X, y)['model']
        residuals = model.resid
        fitted = model.fittedvalues
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Residual vs Fitted
        axes[0,0].scatter(fitted, residuals, alpha=0.5)
        axes[0,0].axhline(y=0, color='r', linestyle='--')
        axes[0,0].set_title('Residuals vs Fitted')
        
        # QQ Plot
        sm.graphics.qqplot(residuals, dist=norm, line='45', ax=axes[0,1])
        axes[0,1].set_title('Normal Q-Q')
        
        # Scale-Location
        axes[1,0].scatter(fitted, np.sqrt(np.abs(residuals)), alpha=0.5)
        axes[1,0].set_title('Scale-Location')
        
        # Residuals vs Leverage
        sm.graphics.influence_plot(model, ax=axes[1,1])
        
        plt.tight_layout()
        return fig