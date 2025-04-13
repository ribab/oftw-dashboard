#!/usr/bin/env python3
# %%
# Average Attrition Rate KPI Card
# This notebook creates a KPI card showing average monthly attrition rate as a Vizro component

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
import vizro.models as vm
import vizro.plotly.express as px
from vizro.models.types import capture
import sys
from pathlib import Path
import calendar

# add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))
from components.kpi_card import create_kpi_card

def calculate_average_attrition_rate(data_frame):
    """
    Calculate average monthly attrition rate
    
    Args:
        data_frame: DataFrame with pledge data
        
    Returns:
        Tuple of (avg_attrition_rate, total_churned, total_months)
    """
    # Make an explicit copy of the filtered DataFrame
    df = data_frame[data_frame['pledge_status'] != 'One-Time'].copy()
    
    # Convert date columns to datetime objects
    df['pledge_created_at'] = pd.to_datetime(df['pledge_created_at'])
    df['pledge_starts_at'] = pd.to_datetime(df['pledge_starts_at'])
    df['pledge_ended_at'] = pd.to_datetime(df['pledge_ended_at'])

    # Get current date for active pledge analysis
    now = pd.Timestamp.now()

    # Get all months from earliest start to latest end or now
    start_date = df['pledge_starts_at'].min()
    end_date = max(df['pledge_ended_at'].max(), now)
    months = pd.date_range(start=start_date, end=end_date, freq='ME')
    
    monthly_rates = []
    total_churned = 0
    
    for month in months:
        month_end = month.replace(day=calendar.monthrange(month.year, month.month)[1])
        month_start = month_end.replace(day=1)
        
        # Count active pledges at start of month
        active_start = df[
            (df['pledge_starts_at'] <= month_start) & 
            ((df['pledge_ended_at'].isna()) | (df['pledge_ended_at'] > month_start))
        ].shape[0]
        
        # Count active pledges at end of month
        active_end = df[
            (df['pledge_starts_at'] <= month_end) & 
            ((df['pledge_ended_at'].isna()) | (df['pledge_ended_at'] > month_end))
        ].shape[0]
        
        # Count churned/failed in this month
        churned_this_month = df[
            (df['pledge_ended_at'].dt.to_period('M') == month_end.to_period('M')) &
            (df['pledge_status'].isin(['Churned donor', 'Payment failure']))
        ].shape[0]
        
        total_churned += churned_this_month
        
        # Calculate average number of pledges for the month
        avg_pledges = (active_start + active_end) / 2
        
        # Calculate attrition rate for this month
        if avg_pledges > 0:
            monthly_rates.append(churned_this_month / avg_pledges * 100)
    
    # Calculate the average monthly attrition rate
    avg_attrition_rate = sum(monthly_rates) / len(monthly_rates) if monthly_rates else 0
    
    return avg_attrition_rate, total_churned, len(monthly_rates)

# Create a custom figure using Dash components
@capture("figure")
def get_figure(data_frame):
    """
    Create a custom KPI figure using dash_bootstrap_components and dash.html
    
    Args:
        data_frame: DataFrame with pledge data
        
    Returns:
        A Dash Bootstrap card component
    """
    avg_attrition_rate, total_churned, total_months = calculate_average_attrition_rate(data_frame)
    target_rate = 18.0
    
    # Determine status
    is_on_target = avg_attrition_rate <= target_rate
    delta = abs(avg_attrition_rate - target_rate)
    status_text = "Lower than target of 18%" if is_on_target else "Higher than target of 18%"
    
    # Format numbers for display
    attrition_formatted = f"{avg_attrition_rate:.1f}%"
    delta_formatted = f"{delta:.1f}%"
    
    # Additional metrics
    additional_metrics = [
        f"{total_churned} total cancelled over {total_months} months",
        f"Average monthly attrition rate"
    ]
    
    # Use the reusable KPI card function
    card = create_kpi_card(
        title="Average Monthly Attrition Rate",
        subtitle="Average % of churned/failed pledges per month",
        value=attrition_formatted,
        target_value=f"{target_rate:.1f}%",
        is_on_target=is_on_target,
        comparison_text=status_text,
        additional_metrics=additional_metrics
    )
    
    return card

# Example usage in a Jupyter notebook
if __name__ == "__main__":
    import pickle
    from vizro import Vizro
    from vizro.managers import data_manager
    
    # reset vizro
    Vizro._reset()
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    
    # Import the load_pledges function from utils.datasource
    from utils.datasource import load_pledges
    from utils.developer_tools import find_available_port
    
    # Load the pledges data
    print("Loading pledges data...")
    pledges_df = load_pledges()
    
    data_manager['pledges'] = load_pledges
    
    # Create a Vizro dashboard with multiple components
    page = vm.Page(
        id="attrition-metrics-page",
        title="Attrition Metrics Dashboard",
        components=[
            # Option 2: Custom Figure component with Bootstrap styling
            vm.Figure(
                id="attrition-kpi-bootstrap",
                figure=get_figure(pledges_df)
            ),
        ]
    )
    
    # Create and run dashboard
    dashboard = vm.Dashboard(pages=[page])
    
    # Run the Vizro dashboard
    Vizro().build(dashboard).run(port=find_available_port())

# %% 