import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(layout="wide", page_title="Epstein Doc Explorer Prototype")

# --- 1. MOCK DATA GENERATOR ---
def get_mock_data():
    nodes = [
        Node(id="Doc_101", label="Court Filing 101", size=25, color="#FF4B4B", type="Document"),
        Node(id="Person_A", label="John Doe", size=15, color="#1C83E1", type="Person"),
        Node(id="Person_B", label="Jane Smith", size=15, color="#1C83E1", type="Person"),
        Node(id="Doc_102", label="Flight Log 2005", size=25, color="#FF4B4B", type="Document"),
    ]
    edges = [
        Edge(source="Person_A", target="Doc_101", label="MENTIONED_IN"),
        Edge(source="Person_B", target="Doc_101", label="MENTIONED_IN"),
        Edge(source="Person_A", target="Doc_102", label="SIGNED"),
    ]
    return nodes, edges

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.title("🔍 Discovery Filters")
selected_type = st.sidebar.multiselect("Filter Node Type:", ["Document", "Person"], default=["Document", "Person"])
min_weight = st.sidebar.slider("Minimum Connectivity:", 0, 10, 1)

# --- 3. THE LAYOUT ---
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Network Visualization")
    nodes, edges = get_mock_data()
    
    # Configure how the graph looks
    config = Config(width=800, height=600, directed=True, physics=True, hierarchical=False)
    
    # Render the graph
    return_value = agraph(nodes=nodes, edges=edges, config=config)

with col2:
    st.subheader("Document Content")
    if return_value:
        st.info(f"Selected: {return_value}")
        st.write("---")
        st.write("This is where the raw text from your SQLite/Neo4j database would appear when you click a node.")
    else:
        st.write("Click a node in the graph to view details.")
