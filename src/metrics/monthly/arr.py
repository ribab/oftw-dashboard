#!/usr/bin/env python3
# %%
# Chapter Annual Recurring Revenue (ARR) Monthly Chart
# This script creates visualizations showing the annual recurring revenue (ARR) 
# by chapter over time, separated by chapter type.
#
# Data source: Pledges dataset
# Target metric: $670,000 total ARR
# 
# Features:
# - Converts all pledges to USD equivalent
# - Calculates pledge status based on date rather than stored status
# - Shows separate charts for each chapter type
# - Shows ARR contribution by chapter within each type at month end

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import calendar


def calculate_monthly_arr(data_frame, start_column, end_column):
    """Calculate ARR for each chapter at each month end using change tracking"""
    data_frame = data_frame.copy()
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

    # Filter out one-time donations
    recurring_pledges = data_frame[data_frame['pledge_status'] != 'One-Time'].copy()
    
    if recurring_pledges.empty:
        print("No recurring pledges found!")
        return pd.DataFrame()

    # Create list of ARR changes when pledges start
    start_changes = pd.DataFrame({
        'date': recurring_pledges[start_column],
        'donor_chapter': recurring_pledges['donor_chapter'],
        'chapter_type': recurring_pledges['chapter_type'],
        'arr_change': recurring_pledges['annualized_usd_amount']
    })

    # Create list of ARR changes when pledges end
    ended_pledges = recurring_pledges[recurring_pledges[end_column].notna() & (recurring_pledges[end_column] != 'NaT')].copy()
    end_changes = pd.DataFrame({
        'date': ended_pledges[end_column],
        'donor_chapter': ended_pledges['donor_chapter'],
        'chapter_type': ended_pledges['chapter_type'],
        'arr_change': -ended_pledges['annualized_usd_amount']  # Negative because pledge is ending
    })

    # Combine start and end changes
    all_changes = pd.concat([start_changes, end_changes]).sort_values('date').reset_index(drop=True)

    # Get current date
    now = datetime.datetime.now()

    # Filter changes to include only dates up to now
    all_changes = all_changes[all_changes['date'] <= now]

    if all_changes.empty:
        print("No changes found in the relevant time period!")
        return pd.DataFrame()

    # Create month-end snapshots
    min_date = all_changes['date'].min()
    max_date = all_changes['date'].max()
    
    # Create list of month-end dates
    month_ends = []
    current_date = pd.Timestamp(min_date.year, min_date.month, 1)
    
    while current_date <= max_date:
        last_day = calendar.monthrange(current_date.year, current_date.month)[1]
        month_end = pd.Timestamp(current_date.year, current_date.month, last_day)
        
        if month_end > now:
            break
            
        month_ends.append(month_end)
        
        if current_date.month == 12:
            current_date = pd.Timestamp(current_date.year + 1, 1, 1)
        else:
            current_date = pd.Timestamp(current_date.year, current_date.month + 1, 1)

    # Calculate cumulative ARR for each chapter at each month end
    monthly_arr = []
    
    for month_end in month_ends:
        # Get all changes up to this month end
        changes_to_date = all_changes[all_changes['date'] <= month_end]
        
        if not changes_to_date.empty:
            # Group by chapter and chapter type, sum the ARR changes
            chapter_arr = changes_to_date.groupby(['donor_chapter', 'chapter_type'])['arr_change'].sum().reset_index()
            
            # Add month info
            chapter_arr['month_end'] = month_end
            chapter_arr['month_label'] = month_end.strftime('%Y-%m')
            
            # Only keep chapters with positive ARR
            chapter_arr = chapter_arr[chapter_arr['arr_change'] > 0]
            
            if not chapter_arr.empty:
                monthly_arr.append(chapter_arr)
    
    return pd.concat(monthly_arr, ignore_index=True) if monthly_arr else pd.DataFrame()

def custom_chart(
        data_frame, start_column, end_column,
        title="Monthly Annual Recurring Revenue (ARR)",
        subtitle="Based on active and future pledges at month end",
        target=None  # Added target parameter
        ):
    """Create charts showing ARR by chapter over time
    
    Args:
        data_frame: Pandas DataFrame with pledge data
        chapter_type: Optional string specifying which chapter type to plot
        target: Optional float specifying the target line value
    """
    data_frame = data_frame.copy()
    # Calculate monthly ARR for all chapters
    monthly_arr_df = calculate_monthly_arr(data_frame, start_column, end_column)
    
    if monthly_arr_df.empty:
        print("No data available for plotting")
        return None

    # Create figure
    fig = go.Figure()
    
    # Group by month and sum the ARR
    monthly_totals = monthly_arr_df.groupby('month_label')['arr_change'].sum().reset_index()
    
    # Sort by month chronologically
    monthly_totals = monthly_totals.sort_values('month_label')
    
    # Add bar chart for total ARR
    fig.add_trace(go.Bar(
        x=monthly_totals['month_label'],
        y=monthly_totals['arr_change'],
        marker_color='#1f77b4',
        text=monthly_totals['arr_change'].apply(lambda x: f"${x:,.0f}"),
        textposition='auto'
    ))

    # Add target line if specified
    if target is not None:
        fig.add_trace(go.Scatter(
            x=monthly_totals['month_label'],
            y=[target] * len(monthly_totals),
            mode='lines',
            line=dict(color='#808080', dash='dash'),  # Changed to gray
        ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': f"{title}<br><i style='font-size:14px'>{subtitle}</i>",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        xaxis_title='Month',
        yaxis_title='Annual Recurring Revenue (USD)',
        template='plotly_white',
        margin=dict(t=80, b=0),
        bargap=0.2,
        showlegend=False  # Hide the legend
    )

    # Update axes
    fig.update_xaxes(tickangle=45)
    fig.update_yaxes(tickformat="$,.0f")

    return fig

if __name__ == "__main__":
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    
    # Import the load_pledges function from utils.datasource
    from src.utils.datasource import load_pledges
    
    # Load the pledges data
    print("Loading pledges data...")
    pledges_df = load_pledges()
    
    # Create and display overall chart
    print("Creating overall ARR chart...")
    fig = custom_chart(pledges_df, 'pledge_created_at', 'pledge_ended_at',
                      target=1800000)  # $1.8M target for ALL ARR
    if fig:
        fig.update_layout(template="plotly_dark")
        fig.show()

    print("Creating future ARR chart...")
    fig = custom_chart(pledges_df, 'pledge_created_at', 'pledge_starts_at',
                      title="Future ARR",
                      subtitle="Based on future pledges at month end",
                      target=600000)  # $600K target for Future ARR
    if fig:
        fig.update_layout(template="plotly_dark")
        fig.show()
    
    print("Creating active ARR chart...")
    fig = custom_chart(pledges_df, 'pledge_starts_at', 'pledge_ended_at',
                      title="Active ARR",
                      subtitle="Based on active pledges at month end",
                      target=1200000)  # $1.2M target for Active ARR
    if fig:
        fig.update_layout(template="plotly_dark")
        fig.show()
# %% 