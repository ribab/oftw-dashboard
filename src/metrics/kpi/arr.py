#!/usr/bin/env python3
# %%
# Annual Recurring Revenue (ARR) KPI Metric
# This script calculates the total Annual Recurring Revenue (ARR) based on active pledges
# and creates a KPI card to display it.
#
# Data source: Pledges dataset
# Target metric: $670,000 total ARR

import pandas as pd
import plotly.graph_objects as go
import datetime
import calendar


def calculate_current_arr(data_frame, start_column, end_column, month=None):
    """Calculate the current total ARR from all active pledges
    
    Args:
        data_frame: Pandas DataFrame with pledge data
        current_date: Optional date to use as the current date for ARR calculation
    Returns:
        float: Total ARR value
    """
    data_frame = data_frame.copy()
    # remove One-Time pledges
    data_frame = data_frame[data_frame['pledge_status'] != 'One-Time']
    # Convert date columns to datetime
    for col in ['pledge_created_at', 'pledge_starts_at', 'pledge_ended_at']:
        data_frame[col] = pd.to_datetime(data_frame[col])
    
    # Convert usd_amount to numeric
    data_frame['usd_contribution_amount'] = pd.to_numeric(data_frame['usd_contribution_amount'], errors='coerce')

    # Calculate annualized amounts based on frequency
    def annualized_amount(row):
        if row['frequency'] == 'Monthly':
            return row['usd_contribution_amount'] * 12
        elif row['frequency'] == 'Quarterly':
            return row['usd_contribution_amount'] * 4
        else:  # Annual
            return row['usd_contribution_amount']

    data_frame['annualized_usd_amount'] = data_frame.apply(annualized_amount, axis=1)

    # Get current date
    if month is None:
        if 'fiscal_year' in data_frame.columns:
            fiscal_year = data_frame.iloc[-1]['fiscal_year']
            month = f"{fiscal_year.split('-')[1]}-06"
        else:
            month = datetime.datetime.now().strftime('%Y-%m')
    
    # filter for pledges with dt >= start_column and dt <= end_column
    if end_column == 'pledge_ended_at':
        active_pledges = data_frame[
            (data_frame[start_column].dt.strftime('%Y-%m') <= month) &
            ((data_frame[end_column].isna()) | (data_frame[end_column].dt.strftime('%Y-%m') > month))
        ]
    else:
        active_pledges = data_frame[
            (data_frame[start_column].dt.strftime('%Y-%m') <= month) &
            (data_frame[end_column].dt.strftime('%Y-%m') > month)
        ]

    if active_pledges.empty:
        print("No active recurring pledges found!")
        return 0
    
    # Sum the annualized amounts to get total ARR
    total_arr = active_pledges['annualized_usd_amount'].sum()
    
    return total_arr


def create_arr_kpi_card(
        data_frame,
        target_arr=1_800_000,
        title="Total ARR",
        subtitle="Active + pledged donors",
        start_column='pledge_created_at',
        end_column='pledge_ended_at',
        month=None
        ):
    """Create a KPI card showing the current ARR and comparison to target
    
    Args:
        data_frame: Pandas DataFrame with pledge data
        target_arr: Target ARR value (default: $1,800,000)
        title: Title for the KPI card (default: "Active ARR + Future ARR")
        subtitle: Subtitle for the KPI card (default: "Total Annualized Recurring Revenue from active and pledged donors")
        comparison_text: Custom comparison text (default: None, will be auto-generated)
        
    Returns:
        A Dash component representing the KPI card
    """
    from components.kpi_card import create_kpi_card
    
    # Calculate current ARR
    current_arr = calculate_current_arr(data_frame, start_column, end_column, month)
    
    # Format values for display
    formatted_arr = f"${current_arr:,.0f}"
    formatted_target = f"${target_arr/1e6:.1f}M"
    
    # Calculate delta and determine if on target
    delta = current_arr - target_arr
    is_on_target = delta >= 0
    
    # Format delta for display
    delta_percent = abs(delta) / target_arr * 100
    formatted_delta = f"{delta_percent:.1f}%"
    
    # Determine comparison text if not provided
    comparison_text = "above target" if is_on_target else "below target"
    # Format target_arr with M suffix for millions
    target_arr_in_millions = target_arr / 1e6
    comparison_text = f"{comparison_text} of ${target_arr_in_millions:.1f}M"
    
    # Count active pledges
    active_pledges_count = len(data_frame)

    # count unique donor_id
    unique_donor_count = data_frame['donor_id'].nunique()

    from dash import html

    # Create the KPI card
    card = create_kpi_card(
        title=title,
        subtitle=subtitle,
        value=formatted_arr,
        is_on_target=is_on_target,
        on_target_msg=f"above {formatted_target} target",
        off_target_msg=f"below {formatted_target} target",
        additional_metrics=[
            f"{active_pledges_count} pledges",
            f"{unique_donor_count} unique donors"
        ]
    )
    
    return card


# | Future ARR | $600,000 | Pledges dataset, 'pledge_status' equals 'Pledged donor', converted to USD | Projected annual value of committed future pledges, converted to USD. |
def create_future_arr_kpi_card(data_frame, target_arr=600_000, month=None):
    """Create a KPI card showing the future ARR from pledged donors
    
    Args:
        data_frame: Pandas DataFrame with pledge data
        target_arr: Target future ARR value (default: $600,000)
        
    Returns:
        A Dash component representing the KPI card
    """
    # Filter for only pledged donors (future ARR)
    # future_pledges_df = data_frame[data_frame['pledge_status'] == 'Pledged donor'].copy()
    
    # Create the KPI card with appropriate title and subtitle
    return create_arr_kpi_card(
        data_frame=data_frame,
        target_arr=target_arr,
        title="Future ARR",
        subtitle="From pledged donors",
        start_column='pledge_created_at',
        end_column='pledge_starts_at',
        month=month
    )


#| Active ARR | $1.2M | Pledges dataset, 'pledge_status' equals 'Active donor', converted to USD | Current annual run rate from active pledges only, in USD. |
def create_active_arr_kpi_card(data_frame, target_arr=1_200_000, month=None):
    """Create a KPI card showing the active ARR from active donors
    
    Args:
        data_frame: Pandas DataFrame with pledge data
        target_arr: Target active ARR value (default: $1,200,000)
        
    Returns:
        A Dash component representing the KPI card
    """
    # Filter for only active donors (active ARR)
    # active_pledges_df = data_frame[data_frame['pledge_status'] == 'Active donor'].copy()
    
    # Create the KPI card with appropriate title and subtitle
    return create_arr_kpi_card(
        data_frame=data_frame,
        target_arr=target_arr,
        title="Active ARR",
        subtitle="From active donors",
        start_column='pledge_starts_at',
        end_column='pledge_ended_at',
        month=month
    )



if __name__ == '__main__':
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
    
    # Calculate and print the current ARR
    current_arr = calculate_current_arr(pledges_df, start_column='pledge_starts_at', end_column='pledge_ended_at')
    print(f"Current ARR: ${current_arr:,.2f}")
    
    # Create a test dashboard to display the KPI card
    import pickle
    from vizro import Vizro
    from vizro.managers import data_manager
    import vizro.models as vm
    from vizro.models.types import capture
    
    # Define a function with the capture decorator
    @capture("figure")
    def get_arr_figure(data_frame):
        """Create a custom ARR KPI figure"""
        return create_arr_kpi_card(data_frame)
    
    @capture("figure")
    def get_future_arr_figure(data_frame):
        """Create a custom Future ARR KPI figure"""
        return create_future_arr_kpi_card(data_frame)
    
    @capture("figure")
    def get_active_arr_figure(data_frame):
        """Create a custom Active ARR KPI figure"""
        return create_active_arr_kpi_card(data_frame)
    
    # Reset Vizro
    Vizro._reset()
    
    # Register data
    def load_data():
        return pledges_df
        
    data_manager['pledges'] = load_data
    
    # Create a Vizro dashboard with the KPI component
    page = vm.Page(
        id="arr-metrics-page",
        title="ARR Metrics Dashboard",
        layout=vm.Layout(
            grid=[[0], [1], [2]],
            row_min_height="250px"
        ),
        components=[
            # Use Figure component with the captured function
            vm.Figure(
                id="arr-kpi-card",
                figure=get_arr_figure(pledges_df)
            ),
            vm.Figure(
                id="future-arr-kpi-card",
                figure=get_future_arr_figure(pledges_df)
            ),
            vm.Figure(
                id="active-arr-kpi-card",
                figure=get_active_arr_figure(pledges_df)
            )
        ]
    )
    
    # Create and run dashboard
    dashboard = vm.Dashboard(pages=[page])
    
    # Run the Vizro dashboard
    Vizro().build(dashboard).run(port=find_available_port())

# %%
