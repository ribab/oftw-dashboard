#!/usr/bin/env python3
# %%
# All-Time Attrition Rate KPI Card
# This notebook creates a KPI card showing all-time attrition rate as a Vizro component

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
import vizro.models as vm
import vizro.plotly.express as px
from vizro.models.types import capture
import sys
from pathlib import Path

# add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))
from components.kpi_card import create_kpi_card

def calculate_attrition_rate(data_frame):
    """
    Calculate ratio of churned/failed pledges vs currently active pledges
    
    Args:
        data_frame: DataFrame with pledge data including pledge_status column
        
    Returns:
        Tuple of (attrition_rate, active_pledges, attrition_pledges)
    """
    # Ensure we have a copy to avoid modifying the original
    df = data_frame[data_frame['pledge_status'] != 'One-Time'].copy()
    
    # Count currently active pledges
    # active_pledges = df[df['pledge_status'] == 'Active donor'].shape[0]
    
    # Count pledges with failed or churned status
    attrition_pledges = df[df['pledge_status'].isin(['Payment failure', 'Churned donor'])].shape[0]
    
    # Calculate attrition rate
    attrition_rate = (attrition_pledges / len(df) * 100)
    
    return attrition_rate, attrition_pledges

# Create a custom figure using Dash components
def get_figure(data_frame):
    """
    Create a custom KPI figure using dash_bootstrap_components and dash.html
    
    Args:
        data_frame: DataFrame with pledge data
        
    Returns:
        A Dash Bootstrap card component
    """
    attrition_rate, attrition_pledges = calculate_attrition_rate(data_frame)
    target_rate = 18.0
    
    # Determine status
    is_on_target = attrition_rate <= target_rate
    delta = abs(attrition_rate - target_rate)
    status_text = "Lower than target of 18%" if is_on_target else "Higher than target of 18%"
    
    # Format numbers for display
    attrition_formatted = f"{attrition_rate:.1f}%"
    delta_formatted = f"{delta:.1f}%"
    
    # Additional metrics
    additional_metrics = [
        f"{attrition_pledges} cancelled / {len(data_frame)} total pledges historically"
    ]
    
    # Use the reusable KPI card function
    card = create_kpi_card(
        title="All-Time Attrition Rate",
        subtitle="% of churned/failed pledges vs all pledges",
        value=attrition_formatted,
        is_on_target=is_on_target,
        on_target_msg=f"below target of {target_rate:.1f}%",
        off_target_msg=f"above target of {target_rate:.1f}%",
        additional_metrics=additional_metrics
    )
    
    return card

# Example usage in a Jupyter notebook
if __name__ == "__main__":
    import pickle
    from vizro import Vizro
    from vizro.managers import data_manager
    
    # reset vizro
    Vizro._reset()
    
    # Import the load_pledges function from utils.datasource
    from utils.datasource import load_pledges
    from utils.developer_tools import find_available_port
    
    # Load the pledges data
    print("Loading pledges data...")
    pledges_df = load_pledges()
    
    data_manager['pledges'] = load_pledges
    
    # Create a Vizro dashboard with multiple components
    page = vm.Page(
        id="attrition-metrics-page",
        title="Attrition Metrics Dashboard",
        components=[
            # Option 2: Custom Figure component with Bootstrap styling
            vm.Figure(
                id="attrition-kpi-bootstrap",
                figure=capture('figure')(lambda data_frame: get_figure(data_frame))(pledges_df)
            ),
        ]
    )
    
    # Create and run dashboard
    dashboard = vm.Dashboard(pages=[page])
    
    # Run the Vizro dashboard
    Vizro().build(dashboard).run(port=find_available_port())

# %%