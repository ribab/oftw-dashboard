#!/usr/bin/env python3
# %%
# Annualized Run Rate Bar Chart
# This notebook creates a bar chart showing annualized run rate by payment channel.

import pandas as pd
import plotly.graph_objects as go
import datetime

def custom_chart(data_frame, month=None, start_column='pledge_created_at', end_column='pledge_ended_at', subtitle=None):
    """Create a bar chart showing annualized run rate by payment channel
    
    Args:
        data_frame: Pandas DataFrame with pledge data
        month: Optional string in 'YYYY-MM' format to calculate ARR for a specific month
        start_column: Column name for pledge start date
        end_column: Column name for pledge end date
        subtitle: Optional subtitle to display under the title
    """
    # Create a copy of the dataframe to avoid SettingWithCopyWarning
    df = data_frame.copy()

    # Convert date columns to datetime
    for col in [start_column, end_column]:
        df[col] = pd.to_datetime(df[col])

    # Get current date if month not specified
    if month is None:
        month = datetime.datetime.now().strftime('%Y-%m')

    # Filter for active pledges based on start and end dates
    if end_column == 'pledge_ended_at':
        active_df = df[
            (df[start_column].dt.strftime('%Y-%m') <= month) &
            ((df[end_column].isna()) | (df[end_column].dt.strftime('%Y-%m') > month))
        ].copy()
    else:
        active_df = df[
            (df[start_column].dt.strftime('%Y-%m') <= month) &
            (~df[end_column].isna() & (df[end_column].dt.strftime('%Y-%m') > month))
        ].copy()

    # Convert usd_amount to numeric, errors='coerce' will turn invalid parsing into NaN
    active_df['usd_contribution_amount'] = pd.to_numeric(active_df['usd_contribution_amount'], errors='coerce')

    # Handle different frequencies to calculate annualized amounts
    def annualized_amount(row):
        if row['frequency'] == 'Monthly':
            return row['usd_contribution_amount'] * 12
        elif row['frequency'] == 'Quarterly':
            return row['usd_contribution_amount'] * 4
        else:
            return row['usd_contribution_amount']  # Treat as annual if not monthly or quarterly

    active_df['annualized_usd_amount'] = active_df.apply(annualized_amount, axis=1)

    # Group by payment platform and sum the annualized amounts
    channel_arr = active_df.groupby('donor_chapter')['annualized_usd_amount'].sum().reset_index()

    # Sort the payment platforms by annualized amount
    channel_arr = channel_arr.sort_values(by='annualized_usd_amount', ascending=False)

    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(x=channel_arr['donor_chapter'], y=channel_arr['annualized_usd_amount'])
    ])

    title = 'Annualized Run Rate by Chapter'
    if month:
        title += f' ({month})'
    if subtitle:
        title += f'<br><span style="font-size: 12px; color: #888;">{subtitle}</span>'

    fig.update_layout(
        title=title,
        xaxis_title='Payment Platform',
        yaxis_title='Annualized USD Amount',
        showlegend=False,  # Remove the legend
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    # Update yaxis to use currency format
    fig.update_yaxes(tickformat="$,.0f")

    return fig

if __name__ == "__main__":
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    
    # Import the load_pledges function from utils.datasource
    from utils.datasource import load_pledges
    
    # Load the pledges data
    print("Loading pledges data...")
    pledges_df = load_pledges()

    # Create and display charts for different scenarios
    
    # 1. Active pledges only
    fig = custom_chart(
        pledges_df, 
        start_column='pledge_starts_at', 
        end_column='pledge_ended_at',
        subtitle='Active pledges only'
    )
    # Set dark theme
    fig.update_layout(template="plotly_dark")
    fig.show()

    # 2. Future pledges only
    fig = custom_chart(
        pledges_df, 
        start_column='pledge_created_at', 
        end_column='pledge_starts_at',
        subtitle='Future pledges only'
    )
    # Set dark theme
    fig.update_layout(template="plotly_dark")
    fig.show()

    # 3. All pledges (active + future)
    fig = custom_chart(
        pledges_df, 
        start_column='pledge_created_at', 
        end_column='pledge_ended_at',
        subtitle='Active and future pledges'
    )
    # Set dark theme
    fig.update_layout(template="plotly_dark")
    fig.show()

# %% 