#!/usr/bin/env python3
# %%
# Monthly Donations Bar Chart
# This notebook creates a bar chart showing monthly donations excluding internal funds.

import pandas as pd
import plotly.graph_objects as go

def custom_chart(data_frame, counterfactual=False, both=False, title='Money Moved (Monthly)'):
    # Exclude internal funds
    df = data_frame[~data_frame['portfolio'].isin(['One for the World Discretionary Fund', 'One for the World Operating Costs'])].copy()

    # Convert 'date' to datetime objects
    df.loc[:, 'date'] = pd.to_datetime(df['date'])

    if counterfactual:
        df['usd_amount'] = df['counterfactuality'] * df['usd_amount']
    
    if both:
        df_counterfactual = df.copy()
        df_counterfactual['usd_amount'] = df_counterfactual['counterfactuality'] * df_counterfactual['usd_amount']

        df_non_counterfactual = df.copy()
        df_non_counterfactual['usd_amount'] = df_non_counterfactual['usd_amount'] - df_non_counterfactual['counterfactuality'] * df_non_counterfactual['usd_amount']

    # Group by month and sum the 'usd_amount'


    if both:
        monthly_counterfactual = df_counterfactual.groupby(pd.Grouper(key='date', freq='M'))['usd_amount'].sum().reset_index()
        monthly_non_counterfactual = df_non_counterfactual.groupby(pd.Grouper(key='date', freq='M'))['usd_amount'].sum().reset_index()

        fig = go.Figure(data=[
            go.Bar(x=monthly_counterfactual['date'], y=monthly_counterfactual['usd_amount'], name='Counterfactual Money Moved'),
            go.Bar(x=monthly_non_counterfactual['date'], y=monthly_non_counterfactual['usd_amount'], name='Non-Counterfactual Money Moved')
        ])
    else:
        monthly_donations = df.groupby(pd.Grouper(key='date', freq='M'))['usd_amount'].sum().reset_index()
        fig = go.Figure(data=[
            go.Bar(x=monthly_donations['date'], y=monthly_donations['usd_amount'], name='Monthly Donations')
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
    import pickle
    # get path to this script
    # path to payments json
    payments_path = "../../cached_payments.pkl"
    # get data
    payments_df = pickle.load(open(payments_path, "rb"))
    # run the chart
    fig = custom_chart(payments_df)
    # Set dark theme
    fig.update_layout(template="plotly_dark")
    fig.show()

    fig = custom_chart(payments_df, counterfactual=True, title='Counterfactual Money Moved (Monthly)')
    # Set dark theme
    fig.update_layout(template="plotly_dark")
    fig.show()

    fig = custom_chart(payments_df, both=True, title='Money Moved (Monthly)')
    # Set dark theme
    fig.update_layout(template="plotly_dark")
    fig.show()

# %% 