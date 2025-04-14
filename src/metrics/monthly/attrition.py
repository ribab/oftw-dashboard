#!/usr/bin/env python3
# %%
# churned_or_failed = pledges_df[(pledges_df['pledge_status'] == 'Churned donor') | (pledges_df['pledge_status'] == 'Payment failure')]

import pandas as pd
import plotly.graph_objects as go
import datetime
import calendar

def attrition_chart(data_frame, title='Monthly Attrition Rate', target=0.18):
    # Make an explicit copy of the filtered DataFrame
    data_frame = data_frame[data_frame['pledge_status'] != 'One-Time'].copy()
    
    # Convert date columns to datetime objects
    data_frame['pledge_created_at'] = pd.to_datetime(data_frame['pledge_created_at'])
    data_frame['pledge_starts_at'] = pd.to_datetime(data_frame['pledge_starts_at'])
    data_frame['pledge_ended_at'] = pd.to_datetime(data_frame['pledge_ended_at'])

    # Get current date for active pledge analysis
    now = pd.Timestamp.now()

    # Group by month to get monthly snapshots
    monthly_data = []
    
    # Get all months from earliest start to latest end or now
    start_date = data_frame['pledge_starts_at'].min()
    end_date = max(data_frame['pledge_ended_at'].max(), now)
    months = pd.date_range(start=start_date, end=end_date, freq='ME')
    
    for month in months:
        month_end = month.replace(day=calendar.monthrange(month.year, month.month)[1])
        month_start = month_end.replace(day=1)
        
        # Count active pledges at start of month
        active_start = data_frame[
            (data_frame['pledge_starts_at'] <= month_start) & 
            ((data_frame['pledge_ended_at'].isna()) | (data_frame['pledge_ended_at'] > month_start))
        ].shape[0]
        
        # Count active pledges at end of month
        active_end = data_frame[
            (data_frame['pledge_starts_at'] <= month_end) & 
            ((data_frame['pledge_ended_at'].isna()) | (data_frame['pledge_ended_at'] > month_end))
        ].shape[0]
        
        # Count churned/failed in this month
        churned_this_month = data_frame[
            (data_frame['pledge_ended_at'].dt.to_period('M') == month_end.to_period('M')) &
            (data_frame['pledge_status'].isin(['Churned donor', 'Payment failure']))
        ].shape[0]
        
        # Calculate average number of employees for the month
        avg_pledges = (active_start + active_end) / 2
        
        # Calculate attrition rate
        attrition_rate = (churned_this_month / avg_pledges * 100) if avg_pledges > 0 else 0
        
        monthly_data.append({
            'month': month_end,
            'active_start': active_start,
            'active_end': active_end,
            'churned': churned_this_month,
            'avg_pledges': avg_pledges,
            'attrition_rate': attrition_rate
        })
    
    # Convert to DataFrame for easier plotting
    monthly_df = pd.DataFrame(monthly_data)
    
    # Create the visualization
    fig = go.Figure()
    
    # Add bars for attrition rate
    fig.add_trace(go.Bar(
        x=monthly_df['month'],
        y=monthly_df['attrition_rate'],
        text=[f"{rate:.1f}%" for rate in monthly_df['attrition_rate']],
        textposition='auto',
        name='Attrition Rate'
    ))
    
    # Add target line (18%)
    fig.add_trace(go.Scatter(
        x=monthly_df['month'],
        y=[target * 100] * len(monthly_df),
        mode='lines',
        name=f'Target: less than {target * 100}%',
        line=dict(color='lightgray', dash='dash', width=2)
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        xaxis_title='Month',
        yaxis_title='Attrition Rate (%)',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.5,
            xanchor="center",
            x=0.5
        ),
        margin=dict(
            t=80,
            b=100,
            l=50,
            r=50
        ),
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=45)
    
    # Set y-axis range to start at 0 and end at max of data or target + 5%
    y_max = max(max(monthly_df['attrition_rate']), target * 100) + 5
    fig.update_yaxes(range=[0, y_max])
    
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
    
    # Create and display the chart
    fig = attrition_chart(pledges_df)
    if fig is not None:
        # Set dark theme for development
        fig.update_layout(template="plotly_dark")
        fig.show()
    else:
        print("No chart generated due to missing data")


# %%
