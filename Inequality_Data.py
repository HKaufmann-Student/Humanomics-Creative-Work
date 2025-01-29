import pandas as pd
import pandas_datareader.wb as wb
import matplotlib.pyplot as plt
import seaborn as sns
from linearmodels.panel import PanelOLS
import statsmodels.api as sm
import os
from datetime import datetime
import numpy as np

# Create a figures directory with timestamp to organize outputs
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
figures_dir = f'figures_{timestamp}'
os.makedirs(figures_dir, exist_ok=True)

# Step 1: Data Acquisition and Preparation

# Define the indicators we need
indicators = {
    'SI.POV.GINI': 'Gini',
    'GC.TAX.TOTL.GD.ZS': 'Tax_Revenue_GDP',
    'NY.GDP.PCAP.CD': 'GDP_per_Capita',
    'SL.UEM.TOTL.ZS': 'Unemployment_Rate',
    'SE.XPD.TOTL.GD.ZS': 'Education_Expenditure',
    'SH.XPD.CHEX.GD.ZS': 'Healthcare_Expenditure',
    'NV.IND.TOTL.ZS': 'Industry_Share',
    'NV.SRV.TOTL.ZS': 'Services_Share',
    'SI.DST.10TH.10': 'Top_10_Share',
    'SI.DST.FRST.20': 'Bottom_20_Share'
}

# Define the years of interest, e.g., 2000 to 2020
years = list(range(2000, 2021))

# Fetch data for a set of countries. For illustration, let's choose OECD countries
# You can modify the list based on your preference
oecd_countries = [
    'AUS', 'AUT', 'BEL', 'CAN', 'CHE', 'CZE', 'DNK', 'EST', 'FIN',
    'FRA', 'DEU', 'GRC', 'HUN', 'ISL', 'IRL', 'ITA', 'JPN', 'LVA',
    'LTU', 'LUX', 'NLD', 'NZL', 'NOR', 'POL', 'PRT', 'SVK', 'SVN',
    'ESP', 'SWE', 'GBR', 'USA'
]

# Fetch the data
data = wb.download(
    indicator=indicators.keys(),
    country=oecd_countries,
    start=2000,
    end=2020,
    errors=None
)

# Rename columns for clarity
data.rename(columns=indicators, inplace=True)

# Drop rows with missing Gini index as it's our primary dependent variable
data.dropna(subset=['Gini'], inplace=True)

# Display the first few rows
print(data.head())

# After loading the data, add these diagnostic prints
print("\nData Diagnostics:")
print("Total rows in dataset:", len(data))
print("\nGini value statistics:")
print(data['Gini'].describe())
print("\nSample of Gini values by country:")
print(data.groupby('country')['Gini'].count().sort_values(ascending=False))

# Step 2: Exploratory Data Analysis (EDA)

# Reset index for plotting
data_reset = data.reset_index()

# Modify the Gini over time plot with better error handling and debugging
def plot_gini_over_time(data):
    plt.figure(figsize=(15, 8))
    
    # Reset the index to get year as a column
    data_plot = data.reset_index()
    
    # Convert year to numeric if it isn't already
    data_plot['year'] = pd.to_numeric(data_plot['year'])
    
    # Sort by country and year
    data_plot = data_plot.sort_values(['country', 'year'])
    
    # Plot for each country
    for country in data_plot['country'].unique():
        country_data = data_plot[data_plot['country'] == country]
        plt.plot(country_data['year'], country_data['Gini'], 
                label=country, alpha=0.5, linewidth=1.5,
                marker='o', markersize=4)
    
    plt.xlabel('Year')
    plt.ylabel('Gini Coefficient')
    plt.title('Gini Coefficient Over Time by Country')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
    plt.tight_layout()
    return plt.gcf()

# Fix for actual vs predicted plot
def plot_actual_vs_predicted(results, data):
    plt.figure(figsize=(10, 8))
    
    # Get actual and predicted values
    actual = results.model.dependent.values2d
    predicted = results.fitted_values.values  # Convert to numpy array
    
    # Ensure we're working with 1D arrays
    actual = actual.ravel()
    predicted = predicted.ravel()
    
    # Remove any NaN values
    mask = ~(np.isnan(actual) | np.isnan(predicted))
    actual = actual[mask]
    predicted = predicted[mask]
    
    # Create the scatter plot
    plt.scatter(actual, predicted, alpha=0.5, color='blue', label='Observations')
    
    # Add the 45-degree line
    min_val = min(actual.min(), predicted.min())
    max_val = max(actual.max(), predicted.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Fit')
    
    # Add labels and title
    plt.xlabel('Actual Gini Coefficient')
    plt.ylabel('Predicted Gini Coefficient')
    plt.title('Actual vs Predicted Gini Coefficients')
    
    # Add R-squared value to plot
    r2 = results.rsquared
    plt.text(0.05, 0.95, f'R² = {r2:.3f}', 
             transform=plt.gca().transAxes,
             bbox=dict(facecolor='white', alpha=0.8))
    
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    return plt.gcf()

# Fix for inequality persistence plot
def plot_inequality_persistence(data):
    plt.figure(figsize=(12, 8))
    
    # Calculate year-to-year changes in Gini
    for country in data.index.get_level_values('country').unique():
        country_data = data.loc[country].sort_index()
        if len(country_data) > 1:  # Only plot if we have multiple years
            gini_current = country_data['Gini'][:-1]
            gini_next = country_data['Gini'][1:]
            
            plt.scatter(gini_current, gini_next, 
                       alpha=0.5, label=country)
    
    # Add 45-degree line
    min_gini = data['Gini'].min()
    max_gini = data['Gini'].max()
    plt.plot([min_gini, max_gini], [min_gini, max_gini], 
             'r--', label='No Change Line')
    
    plt.xlabel('Gini Coefficient (t)')
    plt.ylabel('Gini Coefficient (t+1)')
    plt.title('Inequality Persistence')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
    plt.tight_layout()
    return plt.gcf()

# Correlation matrix
corr = data.corr()

# Fix: Correlation Matrix - show all values
plt.figure(figsize=(12, 10))
# Remove the mask to show all correlations
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', 
            square=True, linewidths=0.5)
plt.title('Correlation Matrix of Economic Indicators')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(f'{figures_dir}/correlation_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

# Step 3: Econometric Modeling

# Prepare panel data
# Set multi-index for panel data: country and year
panel_data = data.copy()
panel_data = panel_data.reset_index()
panel_data['year'] = pd.to_datetime(panel_data['year'], format='%Y')
panel_data.set_index(['country', 'year'], inplace=True)

# Add a constant term for the regression
panel_data = panel_data.assign(Intercept=1)

# Add more relevant controls and interaction terms
panel_data = panel_data.assign(
    # Log transform GDP per capita to handle scale
    log_gdp = np.log(panel_data['GDP_per_Capita']),
    # Interaction between tax and GDP
    tax_gdp_interaction = panel_data['Tax_Revenue_GDP'] * np.log(panel_data['GDP_per_Capita']),
    # Social spending (education + healthcare)
    social_spending = panel_data['Education_Expenditure'] + panel_data['Healthcare_Expenditure']
)

# Update the independent variables
independent = panel_data[[
    'Tax_Revenue_GDP',
    'log_gdp',
    'tax_gdp_interaction',
    'social_spending',
    'Unemployment_Rate',
    'Industry_Share',
    'Services_Share'
]]

# Add entity (country) and time (year) fixed effects
# Using PanelOLS from linearmodels
# Add entity and time dummies automatically
model = PanelOLS(panel_data['Gini'], independent, entity_effects=True, time_effects=True)
results = model.fit(cov_type='clustered', cluster_entity=True)

# Print the summary of the regression
print(results.summary)

# Step 4: Model Evaluation

# Get the fitted values and actual values
actual = panel_data['Gini'].loc[results.fitted_values.index]  # Only select matching indices
predicted = pd.Series(results.fitted_values.squeeze())

# Remove any NaN values
mask = ~(predicted.isna() | actual.isna())
predicted_clean = predicted[mask]
actual_clean = actual[mask]

# Fix: Actual vs Predicted plot with adjusted scale
def create_and_save_plots(data, results, output_dir):
    # Create plots
    gini_time_fig = plot_gini_over_time(data)
    persistence_fig = plot_inequality_persistence(data)
    
    # Save plots
    gini_time_fig.savefig(f'{output_dir}/gini_over_time.png', bbox_inches='tight')
    persistence_fig.savefig(f'{output_dir}/inequality_persistence.png', bbox_inches='tight')
    
    # Close figures to free memory
    plt.close('all')

# Step 5: Additional Visualizations and Analysis

# 1. Box plot of Gini by country
plt.figure(figsize=(15, 6))
sns.boxplot(data=data_reset, x='country', y='Gini')
plt.xticks(rotation=45)
plt.title('Distribution of Gini Index by Country')
plt.tight_layout()
plt.savefig(f'{figures_dir}/gini_distribution_by_country.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Education vs Healthcare spending scatter
plt.figure(figsize=(10, 6))
scatter = plt.scatter(data_reset['Education_Expenditure'], 
                     data_reset['Healthcare_Expenditure'],
                     c=data_reset['Gini'],
                     cmap='RdYlBu_r')
plt.colorbar(scatter, label='Gini Index')
plt.xlabel('Education Expenditure (% of GDP)')
plt.ylabel('Healthcare Expenditure (% of GDP)')
plt.title('Education vs Healthcare Spending\nColor Intensity Shows Gini Index')
plt.tight_layout()
plt.savefig(f'{figures_dir}/education_healthcare_scatter.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Time trends of inequality measures
plt.figure(figsize=(12, 6))
yearly_means = data_reset.groupby('year').agg({
    'Gini': 'mean',
    'Top_10_Share': 'mean',
    'Bottom_20_Share': 'mean'
}).reset_index()

plt.plot(yearly_means['year'], yearly_means['Gini'], label='Gini Index')
plt.plot(yearly_means['year'], yearly_means['Top_10_Share'], label='Top 10% Share')
plt.plot(yearly_means['year'], yearly_means['Bottom_20_Share'], label='Bottom 20% Share')
plt.xlabel('Year')
plt.ylabel('Value')
plt.title('Trends in Inequality Measures Over Time (OECD Average)')
plt.legend()
plt.tight_layout()
plt.savefig(f'{figures_dir}/inequality_trends.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Decomposition by inequality level
# First, create the Inequality_Level column based on Gini values
data_reset['Inequality_Level'] = pd.qcut(data_reset['Gini'], q=3, labels=['Low', 'Medium', 'High'])

# Define indicators to compare
indicators_to_compare = ['Tax_Revenue_GDP', 'Education_Expenditure', 'Healthcare_Expenditure', 'GDP_per_Capita']

fig, axes = plt.subplots(2, 2, figsize=(15, 12))
for idx, indicator in enumerate(indicators_to_compare):
    ax = axes[idx//2, idx%2]
    sns.boxplot(data=data_reset, x='Inequality_Level', y=indicator, ax=ax)
    ax.set_title(f'{indicator} by Inequality Level')
plt.tight_layout()
plt.savefig(f'{figures_dir}/indicators_by_inequality_level.png', dpi=300, bbox_inches='tight')
plt.close()

# 5. Save summary statistics to CSV
summary_stats = data_reset.groupby('country').agg({
    'Gini': ['mean', 'std', 'min', 'max'],
    'Tax_Revenue_GDP': 'mean',
    'Education_Expenditure': 'mean',
    'Healthcare_Expenditure': 'mean',
    'GDP_per_Capita': 'mean'
}).round(2)

print("\nSummary Statistics by Country:")
print(summary_stats)

summary_stats.to_csv(f'{figures_dir}/summary_statistics.csv')

# 6. Inequality persistence plot
def create_and_save_plots(data, results, output_dir):
    # Create plots
    gini_time_fig = plot_gini_over_time(data)
    persistence_fig = plot_inequality_persistence(data)
    
    # Save plots
    gini_time_fig.savefig(f'{output_dir}/gini_over_time.png', bbox_inches='tight')
    persistence_fig.savefig(f'{output_dir}/inequality_persistence.png', bbox_inches='tight')
    
    # Close figures to free memory
    plt.close('all')

# 7. Dynamic correlations plot
def lag_correlation(data, var1, var2, max_lag=5):
    correlations = []
    for lag in range(max_lag + 1):
        # Fix: Use a list instead of implicit tuple for column selection
        corr = data.groupby('country')[[var1, var2]].apply(
            lambda x: x[var1].corr(x[var2].shift(lag))
        ).mean()
        correlations.append(corr)
    return correlations

# Calculate lagged correlations between Tax Revenue and Gini
lags = range(6)
correlations = lag_correlation(data_reset, 'Tax_Revenue_GDP', 'Gini')

plt.figure(figsize=(10, 6))
plt.plot(lags, correlations, marker='o')
plt.xlabel('Lag (years)')
plt.ylabel('Correlation Coefficient')
plt.title('Lagged Correlation: Tax Revenue vs Gini Index')
plt.grid(True)
plt.savefig(f'{figures_dir}/lagged_correlations.png', dpi=300, bbox_inches='tight')
plt.close()

# Print confirmation message
print(f"\nAll figures have been saved to the '{figures_dir}' directory.")

# When you run your analysis, make sure to call:
create_and_save_plots(data, results, figures_dir)