#!/usr/bin/env python3
# %%
# Monthly Donations Bar Chart
# This notebook creates a bar chart showing monthly donations excluding internal funds.

import pandas as pd
import plotly.graph_objects as go

def custom_chart(data_frame, counterfactual=False, both=False, title='Money Moved (Monthly)'):
    # Exclude internal funds
    df = data_frame[~data_frame['portfolio'].isin(['One for the World Discretionary Fund', 'One for the World Operating Costs'])].copy()

    # Convert 'date' to datetime objects and ensure it's the index
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    if counterfactual:
        df['usd_amount'] = df['counterfactuality'] * df['usd_amount']
    
    if both:
        df_counterfactual = df.copy()
        df_counterfactual['usd_amount'] = df_counterfactual['counterfactuality'] * df_counterfactual['usd_amount']

        df_non_counterfactual = df.copy()
        df_non_counterfactual['usd_amount'] = df_non_counterfactual['usd_amount'] - df_non_counterfactual['counterfactuality'] * df_non_counterfactual['usd_amount']

    # Group by month and sum the 'usd_amount'
    if both:
        monthly_counterfactual = df_counterfactual.resample('ME')['usd_amount'].sum()
        monthly_non_counterfactual = df_non_counterfactual.resample('ME')['usd_amount'].sum()

        fig = go.Figure(data=[
            go.Bar(x=monthly_counterfactual.index, y=monthly_counterfactual.values, name='Counterfactual Money Moved'),
            go.Bar(x=monthly_non_counterfactual.index, y=monthly_non_counterfactual.values, name='Non-Counterfactual Money Moved')
        ])
    else:
        monthly_donations = df.resample('ME')['usd_amount'].sum()
        fig = go.Figure(data=[
            go.Bar(x=monthly_donations.index, y=monthly_donations.values, name='Monthly Donations')
        ])

    # Update layout for better presentation
    fig.update_layout(
        title=title,
        xaxis_title='Month',
        yaxis_title='USD Amount',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    # if both, do stacked bar chart
    if both:
        fig.update_layout(barmode='stack')

    return fig

if __name__ == "__main__":
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    
    # Import the load_pledges function from utils.datasource
    from src.utils.datasource import load_payments
    
    # Load the payments data
    print("Loading payments data...")
    payments_df = load_payments()

    # Create and display charts for different scenarios
    fig = custom_chart(payments_df)
    fig.update_layout(template="plotly_dark")
    fig.show()

    fig = custom_chart(payments_df, counterfactual=True, title='Counterfactual Money Moved (Monthly)')
    fig.update_layout(template="plotly_dark")
    fig.show()

    fig = custom_chart(payments_df, both=True, title='Money Moved (Monthly)')
    fig.update_layout(template="plotly_dark")
    fig.show()

# %%