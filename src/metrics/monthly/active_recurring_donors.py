#!/usr/bin/env python3
# %%
# Total Number of Active Pledges Bar Chart
# This notebook creates a bar chart showing the total number of active pledges at the end of each month.

import pandas as pd
import plotly.graph_objects as go
import datetime
import calendar


def custom_chart(data_frame):
    print(f"Initial data shape: {data_frame.shape}")
    print(f"Unique pledge_status values: {data_frame['pledge_status'].unique()}")

    # Convert date columns to datetime objects
    data_frame['pledge_created_at'] = pd.to_datetime(data_frame['pledge_created_at'])
    data_frame['pledge_starts_at'] = pd.to_datetime(data_frame['pledge_starts_at'])
    data_frame['pledge_ended_at'] = pd.to_datetime(data_frame['pledge_ended_at'])

    # Filter for active pledges only - matching exact status 'Active donor'
    active_pledges = data_frame[data_frame['pledge_status'] != 'One-Time'].copy()
    print(f"Active pledges shape: {active_pledges.shape}")
    
    if active_pledges.empty:
        print("No active pledges found!")
        return None

    # Create list #1: pledge_created_at and 1 for each unique donor
    created_list = pd.DataFrame({
        'date': active_pledges['pledge_starts_at'],
        'donor_id': active_pledges['donor_id'],
        'change': 1
    }).drop_duplicates(['date', 'donor_id'])
    print(f"Created list shape: {created_list.shape}")

    # Create list #2: pledge_end_date and -1 for each unique donor, but only for pledges with an end date
    ended_pledges = active_pledges[active_pledges['pledge_ended_at'].notna() & (active_pledges['pledge_ended_at'] != 'NaT')].copy()
    ended_list = pd.DataFrame({
        'date': ended_pledges['pledge_ended_at'],
        'donor_id': ended_pledges['donor_id'],
        'change': -1
    }).drop_duplicates(['date', 'donor_id'])
    print(f"Ended list shape: {ended_list.shape}")

    # Join the two lists together and sort by date
    combined_list = pd.concat([created_list, ended_list]).sort_values('date').reset_index(drop=True)
    print(f"Combined list shape: {combined_list.shape}")

    # Initialize tracking dictionary and results list
    donor_counts = {}  # tracks number of active pledges per donor
    donor_changes = []  # will store the actual change in unique donor status

    # Iterate through combined_list to track state changes
    for _, row in combined_list.iterrows():
        donor_id = row['donor_id']
        date = row['date']
        change = row['change']
        
        # Get current count for this donor (default 0 if not exists)
        prev_count = donor_counts.get(donor_id, 0)
        
        # Update count
        new_count = prev_count + change
        donor_counts[donor_id] = new_count
        
        # Determine if this caused a meaningful state change
        if prev_count == 0 and new_count > 0:
            # Donor became active
            donor_changes.append({'date': date, 'change': 1})
        elif prev_count > 0 and new_count == 0:
            # Donor became inactive
            donor_changes.append({'date': date, 'change': -1})
        else:
            # No change in active status
            donor_changes.append({'date': date, 'change': 0})

    # Convert donor_changes to DataFrame
    changes_df = pd.DataFrame(donor_changes)
    
    # Calculate cumulative sum of changes to get total active donors over time
    changes_df['active_donors'] = changes_df['change'].cumsum()

    # Get current date
    now = datetime.datetime.now()

    # Filter to include only dates up to the current date
    changes_df = changes_df[changes_df['date'] <= now]

    # Create month-end snapshots
    # First, get the earliest and latest dates
    min_date = changes_df['date'].min()
    max_date = changes_df['date'].max()
    
    # Create a list of month-end dates
    month_ends = []
    current_date = pd.Timestamp(min_date.year, min_date.month, 1)
    
    while current_date <= max_date:
        # Get the last day of the current month
        last_day = calendar.monthrange(current_date.year, current_date.month)[1]
        month_end = pd.Timestamp(current_date.year, current_date.month, last_day)
        
        # If this month-end is in the future, break
        if month_end > now:
            break
            
        month_ends.append(month_end)
        
        # Move to the next month
        if current_date.month == 12:
            current_date = pd.Timestamp(current_date.year + 1, 1, 1)
        else:
            current_date = pd.Timestamp(current_date.year, current_date.month + 1, 1)
    
    # Get the active donor count at each month-end
    monthly_counts = []
    for month_end in month_ends:
        # Find the last entry before or on this month-end
        last_entry = changes_df[changes_df['date'] <= month_end].iloc[-1] if not changes_df[changes_df['date'] <= month_end].empty else None
        
        if last_entry is not None:
            monthly_counts.append({
                'date': month_end,
                'month_label': month_end.strftime('%Y-%m'),
                'active_donors': last_entry['active_donors']
            })
    
    # Convert to DataFrame
    monthly_df = pd.DataFrame(monthly_counts)
    
    # Find the first month where active donors exceeds 100
    start_month = monthly_df[monthly_df['active_donors'] > 100]['date'].min()
    if pd.isna(start_month):
        print("Warning: No month found where active donors exceeds 100, using earliest month")
        start_month = monthly_df['date'].min()
    
    # Filter to months after the start month
    monthly_df = monthly_df[monthly_df['date'] >= start_month]
    
    # Create the bar chart
    fig = go.Figure()
    
    # Add bars for each month
    fig.add_trace(go.Bar(
        x=monthly_df['month_label'],
        y=monthly_df['active_donors'],
        text=[f"{count:,.0f}" for count in monthly_df['active_donors']],
        textposition='auto',
        name='Active Pledges'
    ))
    
    # Add a horizontal line at y=850 (based on requirements)
    fig.add_trace(go.Scatter(
        x=monthly_df['month_label'],
        y=[850] * len(monthly_df),
        mode='lines',
        name='Goal: 850 active pledges',
        line=dict(color='lightgray', dash='dash', width=2)
    ))
    
    # Update layout for better readability
    fig.update_layout(
        title={
            'text': 'Donors With Active Pledges Per Month<br><i style="font-size:14px">Includes only active recurring pledges, not one-time donors</i>',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 20
            }
        },
        xaxis_title='Month',
        yaxis_title='Number of Active Pledges',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.4,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=100)  # Add more top margin to accommodate the subtitle
    )
    
    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=45)

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
    
    # run the chart
    fig = custom_chart(pledges_df)
    if fig is not None:
        # Set dark theme
        fig.update_layout(template="plotly_dark")
        fig.show()
    else:
        print("No chart generated due to missing data")

# %% 