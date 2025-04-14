# %%
import os
import pandas as pd
import vizro.plotly.express as px
from vizro import Vizro
import vizro.models as vm
from vizro_ai import VizroAI
from vizro_ai._vizro_ai import ChartPlan
from dotenv import load_dotenv; load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
from dash import html, dcc, ctx, no_update, callback, Output, Input, State, ALL, MATCH
from typing import Literal, Annotated, Tuple
import dash
from pydantic import AfterValidator, Field, PlainSerializer
from vizro.models._action._actions_chain import _action_validator_factory
import dash_bootstrap_components as dbc
import json
import requests
import concurrent.futures
from tqdm import tqdm
import os
from datetime import datetime
# add project root to sys.path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
# Import the logging decorator
from utils.developer_tools import log_function_call, enable_debug_logging

# Enable debug logging
enable_debug_logging()

# Create a custom TextInput component since it's not available in Vizro
class AIGraphGenerator(vm.VizroBaseModel):
    """Custom TextInput component for Vizro."""
    type: Literal["graph_container"] = "graph_container"
    id: str
    title: str = ""
    placeholder: str = ""
    data_frames: dict
    
    @log_function_call
    def build(self):
        self.initialize_callbacks()
        return html.Div([
            html.Div(
                [
                    dbc.Button(
                        "Create New Chart with AI",
                        id=f"{self.id}_open_modal",
                        color="primary",
                        className="mb-3",
                        size="lg",
                        style={'marginRight': '10px'}
                    ),
                    dbc.Button(
                        "Modify Chart with AI",
                        id=f"{self.id}_open_modal_modify",
                        color="info",
                        className="mb-3",
                        size="lg",
                        style={'display': 'none'}  # Initially hidden, will be shown by callback when charts exist
                    ),
                    dbc.Button(
                        "Rename Chart",
                        id=f"{self.id}_open_modal_rename",
                        color="secondary",
                        className="mb-3",
                        size="lg",
                        style={'display': 'none', 'marginLeft': '10px'}  # Initially hidden, will be shown by callback when charts exist
                    ),
                ],
            ),
            dbc.Modal([
                dbc.ModalHeader("Create New Chart with AI"),
                dbc.ModalBody([
                    html.Div([
                        html.Label("Name of chart", className="form-label"),
                        dcc.Input(
                            id=f"{self.id}_name",
                            placeholder="Enter a name for the chart",
                            className="form-control",
                            style={"width": "100%"}
                        )
                    ], className="mb-3"),
                    
                    html.Div([
                        html.Label("Dataset", className="form-label"),
                        dcc.Dropdown(
                            id=f"{self.id}_df",
                            options=[
                                {"label": f"{k[0].upper() + k[1:].lower()} Data", "value": k}
                                for k in self.data_frames.keys()
                            ],
                            placeholder="Select a dataset",
                            className="form-select",
                            optionHeight=50,                    # Taller options for better readability
                            clearable=False                     # Prevent clearing selection
                        )
                    ]),
                    
                    html.Div([
                        html.Label("Query", className="form-label"),
                        dcc.Textarea(
                            id=f"{self.id}_query",
                            placeholder=self.placeholder,
                            className="form-control",
                            style={"width": "100%", "height": "100px"}
                        ),
                        dcc.Markdown(
                            """
                            Enter a natural language description of the visualization you want to create.
                            For example: "Show me a bubble chart of GDP vs life expectancy colored by continent".
                            """,
                            className="text-muted small"
                        )
                    ], className="mb-3"),
                    
                    html.Div([
                        html.Label("Google Gemini API Key", className="form-label"),
                        dcc.Input(
                            id=f"{self.id}_api_key",
                            type="password",
                            placeholder="Enter your Google Gemini API Key",
                            className="form-control",
                            style={"width": "100%"},
                        ),
                        dbc.Tooltip(
                            "Your API key is used only for this session and not stored",
                            target=f"{self.id}_api_key",
                            placement="top"
                        )
                    ], className="mb-3", style={"display": "none" if os.getenv("GOOGLE_API_KEY") else "block"}),

                    html.Div(id=f"{self.id}_error")
                ]),
                dbc.ModalFooter([
                    dbc.Button(
                        "Close",
                        id=f"{self.id}_close_modal",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Generate",
                        id=f"{self.id}_button",
                        color="primary"
                    )
                ])
            ],
            id=f"{self.id}_modal",
            size="lg",
            is_open=False,
            ),

            # Modal for modifying existing charts
            dbc.Modal([
                dbc.ModalHeader("Modify Chart with AI"),
                dbc.ModalBody([
                    html.Div([
                        html.Label("Modification Query", className="form-label"),
                        dcc.Textarea(
                            id=f"{self.id}_modify_query",
                            placeholder="Describe how you want to modify the chart",
                            className="form-control",
                            style={"width": "100%", "height": "100px"}
                        ),
                        dcc.Markdown(
                            """
                            Enter what you'd like to change about the selected chart.
                            For example: "Change the color scheme to viridis" or "Make it a line chart instead".
                            """,
                            className="text-muted small"
                        )
                    ], className="mb-3"),
                    
                    html.Div([
                        html.Label("Google Gemini API Key", className="form-label"),
                        dcc.Input(
                            id=f"{self.id}_modify_api_key",
                            type="password",
                            placeholder="Enter your Google Gemini API Key",
                            className="form-control",
                            style={"width": "100%"}
                        )
                    ], className="mb-3", style={"display": "none" if os.getenv("GOOGLE_API_KEY") else "block"}),

                    html.Div(id=f"{self.id}_modify_error")
                ]),
                dbc.ModalFooter([
                    dbc.Button(
                        "Close",
                        id=f"{self.id}_close_modal_modify",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Apply Modifications",
                        id=f"{self.id}_button_modify",
                        color="primary"
                    )
                ])
            ],
            id=f"{self.id}_modal_modify",
            size="lg",
            is_open=False,
            ),

            # Modal for renaming charts
            dbc.Modal([
                dbc.ModalHeader("Rename Chart"),
                dbc.ModalBody([
                    html.Div([
                        html.Label("New Chart Name", className="form-label"),
                        dcc.Input(
                            id=f"{self.id}_rename_input",
                            placeholder="Enter new name for the chart",
                            className="form-control",
                            style={"width": "100%"}
                        )
                    ], className="mb-3"),
                    html.Div(id=f"{self.id}_rename_error")
                ]),
                dbc.ModalFooter([
                    dbc.Button(
                        "Close",
                        id=f"{self.id}_close_modal_rename",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Rename",
                        id=f"{self.id}_button_rename",
                        color="primary"
                    )
                ])
            ],
            id=f"{self.id}_modal_rename",
            size="lg",
            is_open=False,
            ),

            html.Div(id=f"{self.id}_output"),
            dcc.Store(id=f"{self.id}_store", data=[], storage_type="local"),
        ])

    @log_function_call
    def initialize_callbacks(self):
        @callback(
            Output(f"{self.id}_store", "data", allow_duplicate=True),
            Output(f"{self.id}_error", "children"),
            Output(f"{self.id}_query", "value"),
            Output(f"{self.id}_name", "value"),
            Output(f"{self.id}_df", "value"),
            Input(f"{self.id}_button", "n_clicks"),
            State(f"{self.id}_query", "value"),
            State(f"{self.id}_api_key", "value"),
            State(f"{self.id}_store", "data"),
            State(f"{self.id}_name", "value"),
            State(f"{self.id}_df", "value"),
            prevent_initial_call=True
        )
        def trigger_generate_plot(_, user_query, api_key, generated_plots, name, selected_df):
            api_key_from_env = os.getenv("GOOGLE_API_KEY")
            if api_key_from_env:
                api_key = api_key_from_env
            try:
                if not name:
                    return no_update, dbc.Alert("Please enter a name for the chart", color="danger"), no_update, no_update, no_update
                if not user_query:
                    return no_update, dbc.Alert("Please enter a query", color="danger"), no_update, no_update, no_update
                if not api_key:
                    return no_update, dbc.Alert("Please enter a Google API key", color="danger"), no_update, no_update, no_update
                if not selected_df:
                    return no_update, dbc.Alert("Please select a dataset", color="danger"), no_update, no_update, no_update
                
                result = self.generate_plot(user_query, api_key, selected_df)
                if not generated_plots:
                    generated_plots = []
                    
                # Clear the form on successful submission
                return [{
                    "chart_name": name,
                    "chart_plan": result.model_dump(),
                    "selected_df": selected_df
                }] + generated_plots, None, "", "", None
            except Exception as e:
                return no_update, dbc.Alert(f"Error generating plot: {e}", color="danger"), no_update, no_update, no_update
            
        @callback(
            Output(f"{self.id}_store", "data", allow_duplicate=True),
            Input({"type": "delete_chart_button", "chart_name": ALL, "version": ALL}, "n_clicks"),
            State(f"{self.id}_store", "data"),
            prevent_initial_call=True
        )
        def delete_chart(n_clicks, data):
            if not ctx.triggered_id or not data or all(not nc for nc in n_clicks):
                return no_update
            
            chart_name = ctx.triggered_id["chart_name"]
            version = ctx.triggered_id["version"]
            
            updated_data = []
            for row in data:
                if row["chart_name"] != chart_name:
                    updated_data.append(row)
                else:
                    if version != "root" and "versions" in row:
                        # Delete specific version
                        if len(row["versions"]) > 1:  # Only keep the chart if there are other versions
                            # Find and remove the version with matching version_number
                            row["versions"] = [v for v in row["versions"] if v.get("version_number", 1) != version]
                            # Update the root level chart_plan and selected_df to the latest version
                            latest_version = row["versions"][-1]
                            row["chart_plan"] = latest_version["chart_plan"]
                            row["selected_df"] = latest_version["selected_df"]
                            updated_data.append(row)
                        # If this was the last version, don't add the chart back (effectively deleting it)
                    # If version is "root" or no versions array, delete the entire chart (don't add it back)
            
            return updated_data

        # Add callback to generate charts based on pattern-matching IDs
        @callback(
            Output({"type": "chart_container", "chart_data": MATCH}, "children"),
            Input({"type": "chart_container", "chart_data": MATCH}, "id"),
        )
        def generate_chart_from_id(triggered_id):
            if not triggered_id:
                return no_update
            
            # Parse the chart data from the ID
            chart_data = json.loads(triggered_id["chart_data"])
            return self.generate_chart_from_plan(chart_data)

        @callback(
            Output(f"{self.id}_output", "children"),
            Input(f"{self.id}_store", "data"),
        )
        def update_graph_container(data):
            if not data:
                data = []
            
            # Find the active chart tab - default to first chart if none is marked active
            active_chart = next((row["chart_name"] for row in data if row.get("active_tab")), data[0]["chart_name"] if data else None)
            
            # Initialize counter outside the function to avoid UnboundLocalError
            cur_chart_version_idx = 0
            def get_next_chart_version_idx():
                nonlocal cur_chart_version_idx
                return_val = cur_chart_version_idx
                cur_chart_version_idx += 1
                return return_val

            return html.Div([
                dbc.Tabs([
                    dbc.Tab([
                        # First check if this chart has versions
                        (dbc.Tabs if len(row.get("versions", [row])) > 1 else lambda x: html.Div(x))([
                            (lambda content, version_info: 
                                dbc.Tab(content, **version_info) if len(row.get("versions", [row])) > 1 
                                else html.Div(content)
                            )([
                                dcc.Markdown(version["chart_plan"]["chart_insights"]),
                                dbc.Tabs([
                                    dbc.Tab(
                                        dcc.Loading(
                                            html.Div(
                                                id={
                                                    "type": "chart_container",
                                                    "chart_data": json.dumps({
                                                        "chart_plan": version["chart_plan"],
                                                        "selected_df": version["selected_df"]
                                                    })
                                                },
                                            ),
                                            type="dot"
                                        ),
                                        label="Graph",
                                    ),
                                    dbc.Tab(
                                        dcc.Markdown(
                                            f"{version['chart_plan']['code_explanation']}\n\n"
                                            "```python\n"
                                            f"{version['chart_plan']['chart_code']}\n"
                                            "```"
                                        ),
                                        label="Chart code",
                                    ),
                                    dbc.Tab(
                                        html.Div([
                                            dcc.Markdown(
                                                "This is the data stored in your browser's local storage that was used to generate the chart.\n"
                                                "```json\n"
                                                f'{json.dumps(version, indent=4)}\n'
                                                "```"
                                            ),
                                            html.Br(),
                                            html.Div([
                                                dbc.Button(
                                                    "Delete chart", 
                                                    id={"type": "delete_chart_button", "chart_name": row["chart_name"], "version": version.get("version_number", 0) if "versions" in row else "root"},
                                                    style={"display": "block"}
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span("Warning: This action cannot be undone.", 
                                                                style={"color": "red", "marginLeft": "10px"})
                                                    ],
                                                    id={"type": "delete_warning", "chart_name": row["chart_name"], "version": version.get("version_number", 0) if "versions" in row else "root"},
                                                    style={"marginLeft": "10px", "display": "block"}
                                                ),
                                                dbc.Tooltip(
                                                    "Delete this version of the chart" if "versions" in row else "Delete this chart and all its versions",
                                                    target={"type": "delete_chart_button", "chart_name": row["chart_name"], "version": version.get("version_number", 0) if "versions" in row else "root"},
                                                    placement="top"
                                                ),
                                            ], style={"display": "flex", "alignItems": "center"}),
                                            html.Br(),
                                        ]),
                                        label="Config",
                                    ),
                                ], active_tab='tab-0', id={'type': 'view_tabs', 'chart_version': get_next_chart_version_idx()})
                            ], {'label': 'v' + str(version.get("version_number", 0)), 'tab_id': f'version-{version.get("version_number", 0)}'} if row.get("versions") else {})
                            for version_idx, version in enumerate(row.get("versions", [row]))
                        ], **({'active_tab': f'version-{row.get("active_version", len(row.get("versions", [row])) - 1)}', 'id': f'versions-tabs-{row["chart_name"]}'} if row.get("versions") and len(row['versions']) > 1 else {}))
                    ], label=row["chart_name"], tab_id=row["chart_name"])
                    for i, row in enumerate(data)
                ], active_tab=active_chart, id='charts-tabs')
            ])

        @callback(
            Output({'type': 'view_tabs', 'chart_version': ALL}, 'active_tab'),
            Input({'type': 'view_tabs', 'chart_version': ALL}, 'active_tab'),
            prevent_initial_call=True
        )
        def track_view_tabs(active_view_tabs):
            if not ctx.triggered_id:
                return no_update
            chart_version_idx = ctx.triggered_id['chart_version']
            return [active_view_tabs[chart_version_idx] for _ in active_view_tabs]

        # Add callback to track active tabs
        @callback(
            Output(f"{self.id}_store", "data", allow_duplicate=True),
            Input('charts-tabs', 'active_tab'),
            State(f"{self.id}_store", "data"),
            prevent_initial_call=True
        )
        def track_active_tabs(active_chart_tab, data):
            if not data or not active_chart_tab:
                return no_update
                
            # Store the active tab in the data
            updated_data = []
            for row in data:
                if row["chart_name"] == active_chart_tab:
                    row["active_tab"] = active_chart_tab
                else:
                    # Clear active tab for other charts
                    row.pop("active_tab", None)
                updated_data.append(row)
            
            return updated_data

        # Add callback to control modal visibility
        @callback(
            Output(f"{self.id}_modal", "is_open"),
            [
                Input(f"{self.id}_open_modal", "n_clicks"),
                Input(f"{self.id}_close_modal", "n_clicks"),
                Input(f"{self.id}_button", "n_clicks")
            ],
            [State(f"{self.id}_modal", "is_open")],
            prevent_initial_call=True
        )
        def toggle_modal(open_clicks, close_clicks, submit_clicks, is_open):
            if ctx.triggered_id == f"{self.id}_button":
                # Only close if there were no validation errors
                return False
            if open_clicks or close_clicks:
                return not is_open
            return is_open

        # Add callback to handle chart modification
        @callback(
            Output(f"{self.id}_store", "data", allow_duplicate=True),
            Output(f"{self.id}_modify_error", "children"),
            Output(f"{self.id}_modify_query", "value"),
            Input(f"{self.id}_button_modify", "n_clicks"),
            State(f"{self.id}_modify_query", "value"),
            State(f"{self.id}_modify_api_key", "value"),
            State(f"{self.id}_store", "data"),
            State('charts-tabs', 'active_tab'),
            prevent_initial_call=True
        )
        def modify_chart(_, user_query, api_key, data, active_tab):
            api_key_from_env = os.getenv("GOOGLE_API_KEY")
            if api_key_from_env:
                api_key = api_key_from_env
            try:
                if not user_query:
                    return no_update, dbc.Alert("Please enter modification instructions", color="danger"), no_update
                if not api_key:
                    return no_update, dbc.Alert("Please enter a Google API key", color="danger"), no_update
                if not active_tab:
                    return no_update, dbc.Alert("No chart is currently selected", color="danger"), no_update
                
                # Find the active chart using the active tab
                active_chart = next((row for row in data if row["chart_name"] == active_tab), None)
                if not active_chart:
                    return no_update, dbc.Alert(f"Could not find chart with name: {active_tab}", color="danger"), no_update
                
                # Get the active version
                if "versions" in active_chart:
                    active_version_idx = active_chart.get("active_version", len(active_chart["versions"]) - 1)
                    latest_version = active_chart["versions"][active_version_idx]
                else:
                    latest_version = active_chart
                
                # Generate modified plot using the existing chart plan as context
                result = self.generate_plot(user_query, api_key, latest_version["selected_df"], latest_version["chart_plan"])
                
                # Create new version data with a permanent version number
                new_version = {
                    "chart_plan": result.model_dump(),
                    "selected_df": latest_version["selected_df"],
                    "version_number": max([v.get("version_number", 0) for v in active_chart.get("versions", [active_chart])] + [0]) + 1
                }
                
                # Update the existing chart in the data with version history
                updated_data = []
                for row in data:
                    if row["chart_name"] == active_chart["chart_name"]:
                        # If versions don't exist yet, create initial version list with original and new version
                        if "versions" not in row:
                            row["versions"] = [
                                {
                                    "chart_plan": row["chart_plan"],
                                    "selected_df": row["selected_df"],
                                    "version_number": 0  # Initial version gets number 0
                                },
                                new_version
                            ]
                        else:
                            row["versions"].append(new_version)
                        # Keep the chart_plan and selected_df at root level for backward compatibility
                        row["chart_plan"] = new_version["chart_plan"]
                        row["selected_df"] = new_version["selected_df"]
                        # Set this as the active version
                        row["active_version"] = new_version["version_number"]
                    updated_data.append(row)
                
                return updated_data, None, ""  # Clear the modification query
            except Exception as e:
                return no_update, dbc.Alert(f"Error modifying plot: {e}", color="danger"), no_update

        # Add callback to control modify modal visibility
        @callback(
            Output(f"{self.id}_modal_modify", "is_open"),
            [
                Input(f"{self.id}_open_modal_modify", "n_clicks"),
                Input(f"{self.id}_close_modal_modify", "n_clicks"),
                Input(f"{self.id}_button_modify", "n_clicks")
            ],
            [State(f"{self.id}_modal_modify", "is_open")],
            prevent_initial_call=True
        )
        def toggle_modify_modal(open_clicks, close_clicks, submit_clicks, is_open):
            if ctx.triggered_id == f"{self.id}_button_modify":
                # Only close if there were no validation errors
                return False
            if open_clicks or close_clicks:
                return not is_open
            return is_open

        # Add callback to control modify button visibility
        @callback(
            Output(f"{self.id}_open_modal_modify", "style"),
            Input(f"{self.id}_store", "data"),
            prevent_initial_call=True
        )
        def update_modify_button_visibility(data):
            if not data:
                return {'display': 'none'}
            return {'display': 'inline-block'}

        # Add callback to control rename button visibility
        @callback(
            Output(f"{self.id}_open_modal_rename", "style"),
            Input(f"{self.id}_store", "data"),
            prevent_initial_call=True
        )
        def update_rename_button_visibility(data):
            if not data:
                return {'display': 'none'}
            return {'display': 'inline-block', 'marginLeft': '10px'}

        # Add callback to control rename modal visibility
        @callback(
            Output(f"{self.id}_modal_rename", "is_open"),
            [
                Input(f"{self.id}_open_modal_rename", "n_clicks"),
                Input(f"{self.id}_close_modal_rename", "n_clicks"),
                Input(f"{self.id}_button_rename", "n_clicks")
            ],
            [State(f"{self.id}_modal_rename", "is_open")],
            prevent_initial_call=True
        )
        def toggle_rename_modal(open_clicks, close_clicks, submit_clicks, is_open):
            if ctx.triggered_id == f"{self.id}_button_rename":
                # Only close if there were no validation errors
                return False
            if open_clicks or close_clicks:
                return not is_open
            return is_open

        # Add callback to prefill rename input with current chart name
        @callback(
            Output(f"{self.id}_rename_input", "value", allow_duplicate=True),
            Input(f"{self.id}_open_modal_rename", "n_clicks"),
            State(f"{self.id}_store", "data"),
            prevent_initial_call=True
        )
        def prefill_rename_input(_, data):
            if not data:
                return no_update
            # Find the active chart
            active_chart = next((row for row in data if row.get("active_tab") == row["chart_name"]), None)
            if not active_chart:
                return no_update
            return active_chart["chart_name"]

        # Add callback to handle chart renaming
        @callback(
            Output(f"{self.id}_store", "data", allow_duplicate=True),
            Output(f"{self.id}_rename_error", "children"),
            Output(f"{self.id}_rename_input", "value"),
            Input(f"{self.id}_button_rename", "n_clicks"),
            State(f"{self.id}_rename_input", "value"),
            State(f"{self.id}_store", "data"),
            prevent_initial_call=True
        )
        def rename_chart(_, new_name, data):
            try:
                if not new_name:
                    return no_update, dbc.Alert("Please enter a new name for the chart", color="danger"), no_update
                
                # Find the active chart
                active_chart = next((row for row in data if row.get("active_tab") == row["chart_name"]), None)
                if not active_chart:
                    return no_update, dbc.Alert("No chart is currently selected", color="danger"), no_update
                
                # Check if the new name already exists
                if any(row["chart_name"] == new_name for row in data):
                    return no_update, dbc.Alert("A chart with this name already exists", color="danger"), no_update
                
                # Update the chart name
                updated_data = []
                for row in data:
                    if row["chart_name"] == active_chart["chart_name"]:
                        row["chart_name"] = new_name
                        if row.get("active_tab"):
                            row["active_tab"] = new_name
                    updated_data.append(row)
                
                return updated_data, None, ""  # Clear the rename input
            except Exception as e:
                return no_update, dbc.Alert(f"Error renaming chart: {e}", color="danger"), no_update

    # Define a function to generate plots based on user input
    @log_function_call
    def generate_plot(self, user_query: str, api_key: str, selected_df: str, existing_chart_plan=None):
        """
        Generate a plot based on the user's natural language query using Gemini.
        Returns a plotly figure object.
        
        Parameters:
        - user_query: The user's natural language query
        - api_key: Google API key
        - selected_df: Name of the selected dataframe
        - existing_chart_plan: Optional ChartPlan object for modifications
        """
        # Initialize the Gemini model with langchain
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-001",
            temperature=0,
            google_api_key=api_key
        )

        # Initialize Vizro-AI with the Gemini model
        vizro_ai = VizroAI(model=llm)

        # Get the selected dataframe
        df = self.get_dataframe(selected_df)

        # Define dataframe context based on selection
        df_contexts = {
            "Payments": """
This is the PAYMENTS dataframe tracking individual donation transactions:
- payment_id: Unique transaction identifier
- donor_id: Unique donor identifier
- payment_platform: Platform used [Squarespace, Benevity, Gift Aid, Donational, Off Platform, NFG]
- portfolio: Recipient charity (OFTW recommends 4 top charities)
- currency: Transaction currency [USD, GBP, CAD, AUD, EUR, SGD, CHF]
- date: Transaction date
- counterfactuality: OFTW impact score (0-1) [Values: 0.0, 0.31, 0.68, 0.76, 1.0]
- pledge_id: Links to associated pledge
- usd_amount: Donation amount in USD
- original_amount: Donation in original currency""",
            
            "Pledges": """
This is the PLEDGES dataframe tracking donor commitments:
- donor_id: Unique donor identifier
- pledge_id: Unique pledge identifier
- donor_chapter: Donor's entry point
- chapter_type: Category of entry [Corporate, UG, Grad, Law, MBA, Medical]
- pledge_status: Current state [Active donor, One-Time, Churned donor, Updated, Payment failure, ERROR, Pledged donor]
- pledge_created_at: Creation date
- pledge_starts_at: Activation date
- pledge_ended_at: End date (empty if active)
- currency: Pledge currency [USD, GBP, EUR, AUD, CAD]
- frequency: Payment schedule [One-Time, Annually, Monthly, Quarterly, Semi-Monthly, Unspecified]
- payment_platform: Processing platform
- usd_contribution_amount: Pledged amount in USD
- original_contribution_amount: Pledged amount in original currency""",
            
            "Merged": """
This is the COMBINED dataframe merging payment and pledge information.
Contains all fields from both Payments and Pledges dataframes with these characteristics:
- Null values appear as 'nan'
- Counterfactuality includes 'nan' values
- Chapter_type includes 'nan' values
- Pledge_status includes 'nan' values
- Frequency includes both 'nan' and empty values
- Payment_platform includes 'nan' values
- Currency includes 'nan' values

Key relationships:
- pledge_id links payments to pledges
- donor_id links across all tables
- All monetary amounts are available in both USD and original currency"""
        }

        # If modifying existing chart, include the chart plan in the query
        if existing_chart_plan:
            context = f"""
            I have an existing chart with the following configuration:
            {json.dumps(existing_chart_plan, indent=2)}
            
            Please modify this chart according to the following request:
            {user_query}
            
            Maintain the same basic structure and data while applying the requested changes.

            Additional context about the data:
            {df_contexts.get(selected_df, "")}
            """
            result = vizro_ai.plot(df, context, return_elements=True)
        else:
            context = f"""
            Please create a visualization based on this request:
            {user_query}

            Additional context about the data:
            {df_contexts.get(selected_df, "")}
            """
            result = vizro_ai.plot(df, context, return_elements=True)
        
        return result

    @log_function_call
    def generate_chart_from_plan(self, data):
        chart_plan = data["chart_plan"]
        selected_df = data["selected_df"]
        if "selected_df" in data and data["selected_df"] in self.data_frames:
            df = self.get_dataframe(selected_df)
            fig = ChartPlan(**chart_plan).get_fig_object(df)
            # check if fig is too large to display bytes-wise
            if len(fig.to_json()) > 50_000_000: # no larger than 50MB
                return dbc.Alert("Chart is too large to display", color="danger")
            return dcc.Graph(figure=fig)
        else:
            return dbc.Alert("Invalid dataset", color="danger")
    
    @log_function_call
    def get_dataframe(self, selected_df: str):
        df = self.data_frames[selected_df]
        # if df is a function, call it
        if callable(df):
            df = df()
        elif isinstance(df, str):
            # if a string, use vizro data manager to get the dataframe
            df = vm.data_manager[df].load()
        elif not isinstance(df, pd.DataFrame):
            raise ValueError(f"Invalid dataframe: {type(df)}")
        
        return df

vm.Page.add_type("components", AIGraphGenerator)


if __name__ == "__main__":
    # import datasource.py
    from utils.datasource import *

    Vizro._reset()
    # Create a Vizro page with text input for user queries and a dynamic graph
    page = vm.Page(
        title="AI-Powered Data Visualization",
        components=[
            AIGraphGenerator(
                id="graph_container",
                data_frames={
                    "Pledges": load_pledges,
                    "Payments": load_payments,
                    "Merged": load_merged_payments_and_pledges
                }
            )
        ],
    )

    # Build and run the dashboard
    dashboard = vm.Dashboard(
        pages=[page],
        title="Vizro AI Dashboard"
    )


    app = Vizro().build(dashboard)
    
    # Find an available port
    from utils.developer_tools import find_available_port
    port = find_available_port()
    
    # Run the app on the available port
    app.run(debug=True, port=port)

# %%
