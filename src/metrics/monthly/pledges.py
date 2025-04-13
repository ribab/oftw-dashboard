#!/usr/bin/env python3
# %%
# Total Number of Pledges Bar Chart
# This notebook creates a bar chart showing the total number of all pledges (active + future) at the end of each month.

import pandas as pd
import plotly.graph_objects as go
import datetime
import calendar


def pledges_chart(data_frame, start_column='pledge_created_at', end_column='pledge_ended_at', title='Total Active and Committed Future Pledges Each Month', target=1850):
    # Make an explicit copy of the filtered DataFrame
    data_frame = data_frame[data_frame['pledge_status'] != 'One-Time'].copy()
    print(f"Initial data shape: {data_frame.shape}")
    print(f"Unique pledge_status values: {data_frame['pledge_status'].unique()}")

    # Convert date columns to datetime objects
    data_frame['pledge_created_at'] = pd.to_datetime(data_frame['pledge_created_at'])
    data_frame['pledge_starts_at'] = pd.to_datetime(data_frame['pledge_starts_at'])
    data_frame['pledge_ended_at'] = pd.to_datetime(data_frame['pledge_ended_at'])

    # Get current date for active pledge analysis
    now = pd.Timestamp.now()
    
    print("\nCurrent Active Pledges Analysis:")
    print("-" * 30)
    print("Status counts for currently active pledges:")
    status_counts = data_frame['pledge_status'].value_counts()
    for status, count in status_counts.items():
        print(f"{status}: {count}")
    print(f"Total active pledges: {len(data_frame)}")
    print("-" * 30 + "\n")

    # Filter for pledges with no end date
    active_pledges = data_frame[data_frame['pledge_ended_at'].isna()].copy()
    
    print("\nActive Pledges Analysis (No End Date):")
    print("-" * 30)
    print("Status counts for pledges with no end date:")
    status_counts = active_pledges['pledge_status'].value_counts()
    for status, count in status_counts.items():
        print(f"{status}: {count}")
    print(f"Total active pledges: {len(active_pledges)}")
    print("-" * 30 + "\n")

    created_list = pd.DataFrame({
        'date': data_frame[start_column],
        'change': 1,
        'month': data_frame[start_column].dt.to_period('M')
    })
    print(f"Created list shape: {created_list.shape}")

    # Create list #2: pledge_end_date and -1 for each pledge, but only for pledges with an end date
    mask = data_frame[end_column].notna()
    ended_list = pd.DataFrame({
        'date': data_frame.loc[mask, end_column],
        'change': -1,
        'month': data_frame.loc[mask, end_column].dt.to_period('M')
    })
    print(f"Ended list shape: {ended_list.shape}")

    # Join the two lists together and sort by date
    combined_list = pd.concat([created_list, ended_list]).sort_values('month').reset_index(drop=True)
    print(f"Combined list shape: {combined_list.shape}")

    # Convert dates to month periods and group by month
    monthly_changes = combined_list.groupby('month')['change'].sum().reset_index()
    print(f"Combined list shape: {monthly_changes.shape}")

    # Calculate cumulative sum of changes to get total pledges over time
    monthly_changes['total_pledges'] = monthly_changes['change'].cumsum()
    print(f"Combined list shape: {monthly_changes.shape}")

    # convert month to string for initial sorting
    monthly_changes['month_str'] = monthly_changes['month'].astype(str)
    
    # Create date range for all months
    start_date = pd.Period(monthly_changes['month_str'].min()).to_timestamp()
    end_date = now.to_period('M').to_timestamp()
    all_months = pd.date_range(start=start_date, end=end_date, freq='ME')  # Changed 'M' to 'ME'
    
    # Reindex with all months and forward fill the pledges
    monthly_changes = monthly_changes.set_index('month_str')
    monthly_changes = monthly_changes.reindex(all_months.strftime('%Y-%m'))
    monthly_changes['total_pledges'] = monthly_changes['total_pledges'].ffill()  # Changed fillna(method='ffill') to ffill()
    monthly_changes = monthly_changes.reset_index()
    
    # Ensure we have unique column names
    monthly_changes = monthly_changes.drop(columns=['month']) if 'month' in monthly_changes.columns else monthly_changes
    monthly_changes.rename(columns={'index': 'month'}, inplace=True)
    
    # Create the bar chart
    fig = go.Figure()
    
    # Add bars for each month
    fig.add_trace(go.Bar(
        x=monthly_changes['month'],
        y=monthly_changes['total_pledges'],
        text=[f"{count:,.0f}" for count in monthly_changes['total_pledges']],
        textposition='auto',
        name='Total Pledges'
    ))
    
    # Add a horizontal line at y=1850 (based on requirements)
    fig.add_trace(go.Scatter(
        x=monthly_changes['month'],
        y=[target] * len(monthly_changes),
        mode='lines',
        name='Goal: 1,850 pledges',
        line=dict(color='lightgray', dash='dash', width=2)
    ))
    
    # Update layout for better readability
    fig.update_layout(
        title={
            'text': title,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 20
            }
        },
        xaxis_title='Month',
        yaxis_title='Number of Pledges',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,  # Moved legend down
            xanchor="center",
            x=0.5
        ),
        margin=dict(
            t=100,  # Top margin for title
            b=150,  # Increased bottom margin for x-axis labels and legend
            l=50,   # Left margin
            r=50    # Right margin
        ),
        height=700  # Increased overall height of the figure
    )
    
    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=45)

    # limit the x axis to start when total_pledges > 100
    # first find the month when total_pledges > 100
    month_when_pledges_exceed_100 = monthly_changes[monthly_changes['total_pledges'] > 100]['month'].min()
    # then set the x axis start to this month
    fig.update_xaxes(range=[month_when_pledges_exceed_100, end_date])

    return fig

def future_pledges_chart(data_frame):
    return pledges_chart(data_frame, start_column='pledge_created_at', end_column='pledge_starts_at', title='Total Future Pledges Each Month', target=1000)

def active_pledges_chart(data_frame):
    return pledges_chart(data_frame, start_column='pledge_starts_at', end_column='pledge_ended_at', title='Total Active Pledges Each Month', target=850)

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
    
    # run the chart
    fig = pledges_chart(pledges_df)
    if fig is not None:
        # Set dark theme
        fig.update_layout(template="plotly_dark")
        fig.show()
    else:
        print("No chart generated due to missing data")

    fig = future_pledges_chart(pledges_df)
    if fig is not None:
        fig.update_layout(template="plotly_dark")
        fig.show()
    else:
        print("No chart generated due to missing data")

    fig = active_pledges_chart(pledges_df)
    if fig is not None:
        fig.update_layout(template="plotly_dark")
        fig.show()
    else:
        print("No chart generated due to missing data")
# %%
