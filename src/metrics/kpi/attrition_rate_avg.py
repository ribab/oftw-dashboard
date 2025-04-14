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

def calculate_total_attrition_rate(data_frame, start_date, end_date):
    """
    Calculate total attrition rate
    
    Args:
        data_frame: DataFrame with pledge data
        start_date: Optional start date to calculate for. If None, uses current year
        end_date: Optional end date to calculate for. If None, uses current year
        
    Returns:
        Tuple of (total_attrition_rate, total_churned, total_active)
    """
    # Make an explicit copy of the filtered DataFrame
    df = data_frame[data_frame['pledge_status'] != 'One-Time'].copy()
    
    # Convert date columns to datetime objects
    df['pledge_created_at'] = pd.to_datetime(df['pledge_created_at'])
    df['pledge_starts_at'] = pd.to_datetime(df['pledge_starts_at'])
    df['pledge_ended_at'] = pd.to_datetime(df['pledge_ended_at'])

    # Set start and end dates for the year
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    # Count active pledges at start of year
    active_start = df[
        (df['pledge_starts_at'] <= start_date) & 
        ((df['pledge_ended_at'].isna()) | (df['pledge_ended_at'] > start_date))
    ].shape[0]

    # Count active pledges at end of year
    active_end = df[
        (df['pledge_starts_at'] <= end_date) & 
        ((df['pledge_ended_at'].isna()) | (df['pledge_ended_at'] > end_date))
    ].shape[0]

    # Count total churned/failed in this year
    total_churned = df[
        (df['pledge_ended_at'] >= start_date) &
        (df['pledge_ended_at'] <= end_date) &
        (df['pledge_status'].isin(['Payment failure', 'Churned donor']))
    ].shape[0]

    # Calculate average active pledges for the year
    avg_active = (active_start + active_end) / 2

    # Calculate yearly attrition rate
    if avg_active > 0:
        yearly_rate = (total_churned / avg_active) * 100
    else:
        yearly_rate = 0

    return yearly_rate, total_churned, avg_active

def create_total_attrition_kpi_card(data_frame, start_date=None, end_date=None, target_rate=18.0):
    """
    Create a KPI card showing yearly attrition rate
    
    Args:
        data_frame: DataFrame with pledge data
        year: Optional year to calculate for. If None, uses current year
        target_rate: Target attrition rate (default: 18.0%)
        
    Returns:
        A Dash component representing the KPI card
    """
    if 'fiscal_year' in data_frame.columns:
        start_date = pd.to_datetime(f"{data_frame['fiscal_year'].iloc[-1].split('-')[0]}-07-01")
        end_date = pd.to_datetime(f"{data_frame['fiscal_year'].iloc[-1].split('-')[1]}-06-30")
    # Calculate yearly attrition rate
    attrition_rate, total_churned, avg_active = calculate_total_attrition_rate(data_frame, start_date, end_date)
    
    # Format numbers for display
    attrition_formatted = f"{attrition_rate:.1f}%"
    
    # Determine if on target
    is_on_target = attrition_rate <= target_rate
    
    # Calculate delta from target
    delta = abs(attrition_rate - target_rate)
    delta_formatted = f"{delta:.1f}%"
    
    # Additional metrics
    additional_metrics = [
        f"{total_churned:.0f} cancelled / {avg_active:.0f} avg active pledges"
    ]
    
    # Create the KPI card
    card = create_kpi_card(
        title="Yearly Attrition Rate",
        subtitle="% of churned/failed pledges vs average active pledges",
        value=attrition_formatted,
        is_on_target=is_on_target,
        on_target_msg=f"below target of {target_rate:.1f}%",
        off_target_msg=f"above target of {target_rate:.1f}%",
        additional_metrics=additional_metrics
    )
    
    return card


def calculate_average_attrition_rate(data_frame, start_date=None, end_date=None):
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
    if start_date is None:
        start_date = df['pledge_starts_at'].min()
    if end_date is None:
        end_date = pd.Timestamp.now()

    # Get all months from earliest start to latest end or now
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
def get_figure(data_frame):
    """
    Create a custom KPI figure using dash_bootstrap_components and dash.html
    
    Args:
        data_frame: DataFrame with pledge data
        
    Returns:
        A Dash Bootstrap card component
    """
    if 'fiscal_year' in data_frame.columns:
        start_date = pd.to_datetime(f"{data_frame['fiscal_year'].iloc[-1].split('-')[0]}-07-01")
        end_date = pd.to_datetime(f"{data_frame['fiscal_year'].iloc[-1].split('-')[1]}-06-30")
    else:
        start_date = None
        end_date = None
    avg_attrition_rate, total_churned, total_months = calculate_average_attrition_rate(data_frame, start_date=start_date, end_date=end_date)
    target_rate = 18.0
    
    # Determine status
    is_on_target = avg_attrition_rate <= target_rate
    delta = abs(avg_attrition_rate - target_rate)
    status_text = "Lower than target of 18%" if is_on_target else "Higher than target of 18%"
    
    # Format numbers for display
    attrition_formatted = f"{avg_attrition_rate:.1f}%"
    delta_formatted = f"{delta:.1f}%"
    
    # Additional metrics
    # additional_metrics = [
    #     f"{total_churned} cancelled | {total_months} months",
    # ]
    
    # Use the reusable KPI card function
    card = create_kpi_card(
        title="Avg Attrition Per Month",
        subtitle=f"Average % of churned/failed pledges per month / {total_months} months",
        value=attrition_formatted,
        is_on_target=is_on_target,
        on_target_msg=f"below {target_rate:.1f}% target",
        off_target_msg=f"above {target_rate:.1f}% target",
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
                figure=capture('figure')(lambda data_frame: get_figure(data_frame))(pledges_df)
            ),
        ]
    )
    
    # Create and run dashboard
    dashboard = vm.Dashboard(pages=[page])
    
    # Run the Vizro dashboard
    Vizro().build(dashboard).run(port=find_available_port())

# %% 