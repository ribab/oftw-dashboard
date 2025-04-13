#!/usr/bin/env python3
# %%
# Chapter Annual Recurring Revenue (ARR) Chart
# 
# This script creates visualizations showing the annual recurring revenue (ARR) 
# by chapter, separated by chapter type.
#
# Data source: Pledges dataset
# Target metric: $670,000 total ARR
# 
# Features:
# - Converts all pledges to USD equivalent
# - Includes both currently active and committed future pledges
# - Shows separate charts for each chapter type
# - Shows ARR contribution by chapter within each type

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def custom_chart(data_frame, chapter_type, month=None, start_column='pledge_created_at', end_column='pledge_ended_at', subtitle=None):
    """Create a bar chart for a specific chapter type's ARR
    
    Args:
        data_frame: Pandas DataFrame with pledge data
        chapter_type: String specifying which chapter type to plot (e.g. 'UG', 'Grad', etc.)
    """
    if chapter_type == '':
        chapter_type = '<No chapter type>'
    if month is None:
        month = pd.Timestamp.now().strftime('%Y-%m')
    
    # Create a copy of the dataframe to avoid SettingWithCopyWarning
    df = data_frame.copy()
    
    # replace empty string for chapter_type with '<No chapter type>'
    df.loc[:, 'chapter_type'] = df['chapter_type'].fillna('<No chapter type>').replace('', '<No chapter type>')

    # Filter for active donors only
    active_df = df[(pd.to_datetime(df[start_column]).dt.strftime('%Y-%m') <= month) & 
                  ((df[end_column] == '') | (pd.to_datetime(df[end_column]).dt.strftime('%Y-%m') > month))].copy()

    # Convert usd_amount to numeric
    active_df.loc[:, 'usd_contribution_amount'] = pd.to_numeric(active_df['usd_contribution_amount'], errors='coerce')

    # Calculate annualized amounts based on frequency
    def annualized_amount(row):
        if row['frequency'] == 'Monthly':
            return row['usd_contribution_amount'] * 12
        elif row['frequency'] == 'Quarterly':
            return row['usd_contribution_amount'] * 4
        else:  # Annual
            return row['usd_contribution_amount']

    active_df.loc[:, 'annualized_usd_amount'] = active_df.apply(annualized_amount, axis=1)

    # Group by chapter and chapter type, sum the annualized amounts
    chapter_arr = active_df.groupby(['donor_chapter', 'chapter_type'])['annualized_usd_amount'].sum().reset_index()
    
    # Filter for specific chapter type and sort
    df_type = chapter_arr[chapter_arr['chapter_type'] == chapter_type].copy()
    df_type = df_type.sort_values('annualized_usd_amount', ascending=False)

    # Colors for consistency
    colors = {
        'UG': '#1f77b4',  # Blue
        'Grad': '#2ca02c',  # Green
        'Professional': '#ff7f0e',  # Orange
        'Other': '#d62728'  # Red
    }

    # Create the bar chart
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=df_type['donor_chapter'],
            y=df_type['annualized_usd_amount'],
            text=[f"${val:,.0f}" for val in df_type['annualized_usd_amount']],
            textposition='auto',
            marker_color=colors.get(chapter_type, '#7f7f7f'),
            showlegend=False
        )
    )

    title = f'Annual Recurring Revenue - {chapter_type} Chapters'
    if subtitle:
        title += f'<br><span style="font-size: 12px; color: #888;">{subtitle}</span>'

    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Chapter',
        yaxis_title='Annual Recurring Revenue (USD)',
        template='plotly_white',
        height=400,
        margin=dict(t=50, b=0)
    )

    # Update axes
    fig.update_xaxes(tickangle=45)
    fig.update_yaxes(tickformat="$,.0f")

    return fig

if __name__ == "__main__":
    # Import necessary modules
    import sys
    from pathlib import Path
    import pandas as pd
    
    # Add the project root to the path to import from src
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    
    # Import the load_pledges function from utils.datasource
    from src.utils.datasource import load_pledges
    
    # Load the pledges data
    print("Loading pledges data...")
    pledges_df = load_pledges()
    
    # Get all unique chapter types
    chapter_types = sorted(pledges_df['chapter_type'].unique())
    
    # Create and display a chart for each chapter type
    for chapter_type in chapter_types:
        fig = custom_chart(pledges_df, chapter_type, subtitle='Active and future pledges')
        # Set dark theme
        fig.update_layout(template="plotly_dark")
        fig.show()

    for chapter_type in chapter_types:
        fig = custom_chart(pledges_df, chapter_type, subtitle='Active pledges only', start_column='pledge_starts_at')
        # Set dark theme
        fig.update_layout(template="plotly_dark")
        fig.show()

    for chapter_type in chapter_types:
        fig = custom_chart(pledges_df, chapter_type, subtitle='Future pledges only', end_column='pledge_starts_at')
        # Set dark theme
        fig.update_layout(template="plotly_dark")
        fig.show()

# %%
