import pandas as pd
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

df = pd.DataFrame()
app = dash.Dash(__name__)
port = 3000
server_running = False
lock = threading.Lock()

def load_file():
    global df
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", True)

    file_path = filedialog.askopenfilename(
        title="Select Dataset File",
        filetypes=[("CSV Files", "*.csv")]
    )
    if not file_path:
        messagebox.showinfo("No File Selected", "No file was selected. Please try again.")
        return

    try:
        new_df = pd.read_csv(file_path)
        with lock:
            global df
            df = new_df.copy()
        messagebox.showinfo("File Loaded", f"File loaded successfully: {file_path}")
        print(f"File loaded successfully: {file_path}")
    except Exception as e:
        messagebox.showerror("File Load Error", f"Error loading file: {e}")

def start_server():
    global server_running, port

    if server_running:
        messagebox.showinfo("Server Running", f"Server is already running on port {port}.")
        return

    def run():
        global server_running
        try:
            app.run_server(host="0.0.0.0",debug=False, port=port, use_reloader=False)
        except Exception as e:
            print(f"Error starting server: {e}")
        finally:
            server_running = False

    server_thread = threading.Thread(target=run, daemon=True)
    server_thread.start()
    server_running = True
    print(f"Server started on port {port}")

# Tkinter control panel
def tkinter_control_panel():
    root = tk.Tk()
    root.title("Control Panel")
    root.geometry("400x200")

    tk.Label(root, text="Dash App Control Panel", font=("Arial", 16)).pack(pady=10)

    tk.Button(root, text="Load File", command=load_file, width=20).pack(pady=5)
    tk.Button(root, text="Start Server", command=start_server, width=20).pack(pady=5)

    tk.Button(root, text="Exit", command=root.destroy, width=20).pack(pady=20)

    root.mainloop()

# Dash app layout
app.layout = html.Div([
    html.H1("System Metrics Visualizer"),
    
    html.Div([
        html.Label("Select Metrics to Compare on a Single Graph:"),
        dcc.Dropdown(
            id="multi-metrics-dropdown",
            multi=True,
            placeholder="Select metrics",
        ),
    ], style={"margin-bottom": "20px"}),

    html.Div([
        html.Label("Multi-Metric Graph:"),
        dcc.Graph(id="multi-object-graph")
    ]),
])

# Callback to update dropdown options dynamically
@app.callback(
    Output("multi-metrics-dropdown", "options"),
    Input("multi-metrics-dropdown", "id")  # Dummy input to trigger updates
)
def update_dropdown_options(_):
    with lock:
        if df.empty:
            return []
        return [{"label": col, "value": col} for col in df.columns if df[col].dtype != 'object']

# Callback to update the multi-metric graph
@app.callback(
    Output("multi-object-graph", "figure"),
    [Input("multi-metrics-dropdown", "value")]
)
def update_multi_object_graph(selected_metrics):
    with lock:
        if df.empty:
            return px.scatter(title="No data loaded. Please load a valid file.")
        if not selected_metrics:
            return px.scatter(title="Select metrics to compare.")
    
        fig = px.line()
        for metric in selected_metrics:
            fig.add_scatter(x=df.index, y=df[metric], mode="lines", name=metric)
        fig.update_layout(title="Multi-Metric Comparison")
        return fig

if __name__ == "__main__":
    tkinter_control_panel()
