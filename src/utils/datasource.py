#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
from typing import Tuple
from pathlib import Path
import pandas as pd
import json
import concurrent.futures
from datetime import datetime
from tqdm import tqdm

# Load environment variables (for API keys)
load_dotenv()

# get project root using pathlib
project_root = Path(__file__).parent.parent.parent

# Get file paths from environment variables
payments_path = project_root / 'one-for-the-world-payments.json'
pledges_path = project_root / 'one-for-the-world-pledges.json'

if not os.path.exists(payments_path):
    project_root = Path(__file__).parent.parent
    payments_path = project_root / 'one-for-the-world-payments.json'
    pledges_path = project_root / 'one-for-the-world-pledges.json'

cached_payments_path = os.path.join(os.path.dirname(payments_path), 'cached_payments.pkl')
cached_pledges_path = os.path.join(os.path.dirname(pledges_path), 'cached_pledges.pkl')

def fetch_exchange_rate(date_currency: Tuple[str, str]) -> Tuple[Tuple[str, str], float]:
    """Fetch exchange rate for a given date and currency pair."""
    date, currency = date_currency
    if currency == 'USD':
        return (date, currency), 1.0
    
    try:
        response = requests.get(f'https://api.frankfurter.dev/v1/{date}?base={currency}&symbols=USD')
        if response.status_code == 200:
            data = response.json()
            return (date, currency), data['rates']['USD']
        else:
            print(f"Error fetching rate for {currency} on {date}: {response.status_code}")
            return (date, currency), None
    except Exception as e:
        print(f"Error fetching rate for {currency} on {date}: {e}")
        return (date, currency), None

def convert_amounts_to_usd(csv_path, cached_path, date_column, amount_column):
    if os.path.exists(cached_path):
        df = pd.read_pickle(cached_path)
    else:
        with open(csv_path, 'r') as f:
            df = pd.DataFrame(json.load(f))
        # Add currency conversion columns
        
        # Group by date and currency to minimize API calls
        unique_date_currency = df[[date_column, 'currency']].drop_duplicates()
        
        # Get exchange rates for each date-currency pair using parallel processing
        print("Fetching exchange rates...")
        exchange_rates = {}
        today = datetime.now().strftime("%Y-%m-%d")
        date_currency_pairs = [(row[date_column] if row[date_column] <= today else today, row['currency']) for _, row in unique_date_currency.iterrows()]
        
        # Use ThreadPoolExecutor for parallel API requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Create a progress bar that will update as futures complete
            futures = {executor.submit(fetch_exchange_rate, pair): pair for pair in date_currency_pairs}
            
            for future in tqdm(concurrent.futures.as_completed(futures), 
                            total=len(date_currency_pairs),
                            desc="Fetching exchange rates"):
                key, rate = future.result()
                exchange_rates[key] = rate
        
        # Apply exchange rates to get USD amounts
        def get_usd_amount(row):
            if pd.isna(row[amount_column]):  # Handle missing amounts
                return None
            if row['currency'] == 'USD':
                return row[amount_column]
            date = row[date_column] if row[date_column] <= today else today
            rate = exchange_rates.get((date, row['currency']))
            if rate is not None:
                return row[amount_column] * rate
            return None
        
        print("Converting amounts to USD...")
        df[f'usd_{amount_column}'] = df.apply(get_usd_amount, axis=1)

        # Renaming columns
        df[f'original_{amount_column}'] = df[amount_column]
        df = df.drop(columns=[amount_column])
        
        # Cache the processed dataframe
        print("Saving cached dataframe...")
        df.to_pickle(cached_path)
    return df

def __load_pledges():
    df = convert_amounts_to_usd(pledges_path, cached_pledges_path, 'pledge_starts_at', 'contribution_amount')
    # remove errors that have no end date
    # df = df[~(df['pledge_status'].isin(['ERROR', 'Payment failure', 'Churned donor', 'Updated']) & (df['pledge_ended_at'] == ''))]
    df = df[~(df['pledge_status'].isin(['ERROR', 'Payment failure', 'Churned donor']) & (df['pledge_ended_at'] == ''))]
    return df

def load_pledges():
    pledges_df = __load_pledges()
    # filter out where pledge_status = 'Updated'
    combined_df = load_merged_payments_and_pledges(payments_func=load_payments, pledges_func=__load_pledges)
    last_payments = (
        combined_df.groupby('pledge_id').agg({
            'date': 'max',  # Get the latest date
            'payment_id': 'count',
        }).reset_index()
    )
    # use the above code as inpiration on how we can update the missing pledge_ended_at values with the latest date per pledge_id
    # the end result we want a pledges dataframe with this updated column
    df = pd.merge(pledges_df, last_payments, on='pledge_id', how='left')
    df.rename(columns={'payment_id': 'payment_count', 'date': 'last_payment_date'}, inplace=True)
    # update pledge_ended_at with the last payment date if it is missing
    # Create a mask for 'Updated' status
    mask = df['pledge_status'] == 'Updated'
    # Replace empty strings with NA and fill NA with last_payment_date only for 'Updated' status
    df.loc[mask, 'pledge_ended_at'] = df.loc[mask, 'pledge_ended_at'].replace('', pd.NA).fillna(df.loc[mask, 'last_payment_date'])
    # filter out rows where pledge_status = 'Updated' and payment_count is 0
    df = df[~((df['pledge_status'] == 'Updated') & (df['payment_count'] == 0))]

    df = df[list(pledges_df.columns) + ['payment_count', 'last_payment_date']]
    df = df[~((df['payment_count'] == 0) & (df['pledge_status'] != 'Pledged donor'))]
    return df

def load_payments():
    df = convert_amounts_to_usd(payments_path, cached_payments_path, 'date', 'amount')
    df.rename(columns={'id': 'payment_id'}, inplace=True)
    return df

def load_merged_payments_and_pledges(payments_func=load_payments, pledges_func=load_pledges):
    df = pd.merge(payments_func(), pledges_func(), on='pledge_id', how='outer')
    # Handle duplicate columns from the merge
    # For columns ending with '_x', use these values and rename to the original column name
    for col in ['donor_id', 'payment_platform', 'currency']:
        if f'{col}_x' in df.columns and f'{col}_y' in df.columns:
            # Keep the _x version and drop the _y version
            df[col] = df[f'{col}_x']
            df = df.drop(columns=[f'{col}_x', f'{col}_y'])
    return df