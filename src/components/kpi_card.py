#!/usr/bin/env python3
# KPI Card Component
# Reusable component for creating KPI cards with consistent styling
# %%

import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


def create_kpi_card(title, subtitle, value, is_on_target, on_target_msg, off_target_msg, additional_metrics=None):
    """
    Create a reusable KPI card with consistent styling
    
    Args:
        title: Main title of the KPI card
        subtitle: Subtitle or description text
        value: The main KPI value to display
        is_on_target: Boolean indicating if the KPI is meeting target
        on_target_msg: Message to display if the KPI is on target
        off_target_msg: Message to display if the KPI is off target
        additional_metrics: Optional list of strings for additional metrics
        
    Returns:
        A Dash Bootstrap card component
    """
    # Determine status styling
    status_color = "success" if is_on_target else "danger"
    
    # Create the card
    card = dbc.Card(
        [
            dbc.CardBody(
                [
                    # Title and subtitle
                    html.H3(title, className="card-title mb-0 text-center p-1"),
                    html.P(subtitle, className="text-muted small mb-0 text-center p-1"),
                    
                    # Main KPI value (large percentage)
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Div(
                                    value,
                                    className="text-center fw-bold p-1",
                                    style={"fontSize": "2rem"}
                                ),
                                width=12,
                                className="text-center"
                            ),
                        ],
                        className="m-0"
                    ),
                    
                    # Info text (e.g. "5093 cancelled / 11911 total")
                    dbc.Row(
                        html.Div(
                            [
                                html.Div(m, className="p-1")
                                for m in additional_metrics
                            ] if isinstance(additional_metrics, list) else additional_metrics,
                            className="text-muted small mb-0 text-center d-flex flex-column"
                        ),
                        className="text-center m-0"
                    ) if additional_metrics else html.Div(),
                    
                    # Status text (e.g. "24.8% more attrition than target")
                    dbc.Row(
                        dbc.Col(
                            html.P(
                                f"{on_target_msg if is_on_target else off_target_msg}",
                                className=f"text-center text-{status_color} p-1"
                            ),
                            width=12,
                            className="text-center"
                        ),
                        className="text-center m-0"
                    ),
                ],
                className="d-flex flex-column justify-content-center align-items-center p-2",
                style={"margin": "0px", "padding": "0px"}
            )
        ],
        className="h-100 shadow-sm",
        style={"border-radius": "15px", "color": "white", "overflow": "auto", "margin": "0px", "padding": "0px"}
    )
    
    return card

# Example usage in a Jupyter notebook
if __name__ == "__main__":
    import pandas as pd
    import dash_bootstrap_components as dbc
    from dash import html
    import vizro.models as vm
    from vizro import Vizro
    from vizro.models.types import capture
    import socket

    # add project root to sys.path
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.developer_tools import find_available_port

    @capture("figure")
    def example_card(data_frame):
        return create_kpi_card(
            title="Example KPI Metric",
            subtitle="Sample metric description",
            value="75.5%",
            is_on_target=False,
            on_target_msg="above target",
            off_target_msg="below target",
            additional_metrics=["755 / 1000 total"]
        )

    Vizro._reset()
    
    # Create a Vizro dashboard with the KPI card
    page = vm.Page(
        id="kpi-example-page",
        title="KPI Card Example",
        components=[
            vm.Figure(
                id="example-kpi-card",
                figure=example_card(pd.DataFrame())
            )
        ]
    )
    
    dashboard = vm.Dashboard(pages=[page])
    
    # run the dashboard
    Vizro().build(dashboard).run(port=find_available_port())

# %%
