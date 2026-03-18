import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(layout="wide")
st.title("📊 Graph Comparative Standings")

DATA_PATH = Path("Output")

GRAPH_NAMES = ["g", "g_no_epstein", "g_bi_simple", "g_dual"]


# ------------------------
# LOAD ALL GRAPHS
# ------------------------
@st.cache_data
def load_graph(graph_name):
    nodes = pd.read_parquet(DATA_PATH / f"{graph_name}_nodes.parquet")
    edges = pd.read_parquet(DATA_PATH / f"{graph_name}_edges.parquet")
    return nodes, edges

@st.cache_data
def load_global_metrics(graph_name):
    path = DATA_PATH / f"{graph_name}_global_metrics.csv"
    return pd.read_csv(path)






# ------------------------
# SIDEBAR CONTROLS
# ------------------------



st.sidebar.header("Controls")


selected_graphs_global = st.sidebar.multiselect(
    "Select Graphs for Global Statistics",
    GRAPH_NAMES,
    default=["g"],
    key="global"
)

selected_graphs = st.sidebar.multiselect(
    "Select Graphs (max 3 for nodes comparison)",
    GRAPH_NAMES,
    default=["g"]
)

top_n = st.sidebar.slider("Top N", 5, 50, 20)






# ------------------------
# NODE STANDINGS
# ------------------------




if selected_graphs_global:

    cols_global = st.columns(len(selected_graphs_global))

    for i, graph_name in enumerate(selected_graphs_global):

        df_global = load_global_metrics(graph_name)

        # Round numeric columns
        numeric_cols = df_global.select_dtypes(include="number").columns
        df_global[numeric_cols] = df_global[numeric_cols].round(3)

        cols_global[i].subheader(graph_name)

        # Transpose for nicer vertical view
        df_display = df_global.T
        df_display.columns = ["Value"]



#        cols_global[i].dataframe(
#            df_display,
#            width="stretch"
#        )
	
	

    for col_name in df_global.columns:
        value = df_global[col_name].iloc[0]
        cols_global[i].metric(col_name, value)
	



st.header("🟢 Node Standings")

if selected_graphs:

    # Load first graph to detect metric columns
    sample_nodes, _ = load_graph(selected_graphs[0])

    # Remove non-metric columns
    exclude_cols = ["x", "y", "id", "name"]
    metric_columns = [
        col for col in sample_nodes.columns
        if col not in exclude_cols and sample_nodes[col].dtype != "object"
    ]

    selected_metric = st.selectbox(
        "Select Metric",
        metric_columns
    )

    cols = st.columns(len(selected_graphs))

    for i, graph_name in enumerate(selected_graphs):

        df_nodes, _ = load_graph(graph_name)

        ranking = (
            df_nodes
            .sort_values(selected_metric, ascending=False)
            [["name", selected_metric]]
            .head(top_n)
        )

        cols[i].subheader(f"{graph_name}")
        cols[i].dataframe(ranking, use_container_width=True)


# ------------------------
# EDGE STANDINGS
# ------------------------
selected_graphs_edges = st.multiselect(
    "Select 2 Graphs for Edge Comparison",
    GRAPH_NAMES,
    default=["g"],
    key="edges"
)

if selected_graphs_edges:

    with st.expander("Edge Comparison Settings", expanded=False):

        sample_nodes, sample_edges = load_graph(selected_graphs_edges[0])

        exclude_cols_edges = ["source", "target"]

        edge_metric_columns = [
            col for col in sample_edges.columns
            if col not in exclude_cols_edges
            and pd.api.types.is_numeric_dtype(sample_edges[col])
        ]

        selected_edge_metric = st.selectbox(
            "Select Edge Metric",
            edge_metric_columns
        )

        show_action = st.checkbox("Show action column")
        show_doc_id = st.checkbox("Show doc_id column")

    # Layout AFTER expander
    cols_edges = st.columns(len(selected_graphs_edges))

    for i, graph_name in enumerate(selected_graphs_edges):

        _, df_edges = load_graph(graph_name)

        ranking_edges = (
            df_edges
            .sort_values(selected_edge_metric, ascending=False)
            .head(top_n)
            .copy()
        )

        # Round numeric columns
        numeric_cols = ranking_edges.select_dtypes(include="number").columns
        ranking_edges[numeric_cols] = ranking_edges[numeric_cols].round(3)

        cols_to_show = ["source", "target", selected_edge_metric]

        if show_action and "action" in ranking_edges.columns:
            cols_to_show.append("action")

        if show_doc_id and "doc_id" in ranking_edges.columns:
            cols_to_show.append("doc_id")

        cols_edges[i].subheader(graph_name)

        cols_edges[i].dataframe(
            ranking_edges[cols_to_show],
            width="stretch"
        )


st.header("🔍 Node Search")
# Input for node name
node_search = st.text_input("Enter node name to search")
# Select graphs to search (default to all graphs)
selected_graphs_search = st.multiselect(
    "Select Graphs to Search",
    GRAPH_NAMES,
    default=GRAPH_NAMES
)

if node_search:
    # If graphs are selected, use the first to list available columns
    if selected_graphs_search:
        sample_nodes_search, _ = load_graph(selected_graphs_search[0])
        # Define which attributes are eligible (exclude id/name if not needed)
        exclude_cols = ["id", "name", "x", "y"]
        attr_columns = [
            col for col in sample_nodes_search.columns
            if col not in exclude_cols
        ]
    else:
        attr_columns = []

    # Let user pick which attributes to show
    selected_attrs = st.multiselect(
        "Select Node Attributes to Display",
        attr_columns,
        default=attr_columns  # default could be all or none
    )

    # If attributes are chosen and graphs are selected, search nodes
    if selected_attrs and selected_graphs_search:
        results = []
        for graph_name in selected_graphs_search:
            df_nodes, _ = load_graph(graph_name)
            # Exact match on name (case-sensitive); adjust if needed
            match = df_nodes[df_nodes['name'] == node_search]
            if not match.empty:
                # Collect values for the selected attributes
                entry = {"Graph": graph_name}
                for attr in selected_attrs:
                    entry[attr] = match.iloc[0][attr]
                results.append(entry)

        # Display results
        if results:
            df_results = pd.DataFrame(results)
            st.dataframe(df_results, use_container_width=True)
        else:
            st.warning(f"No node named '{node_search}' found in selected graphs.")
