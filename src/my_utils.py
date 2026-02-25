import pandas as pd
from collections import Counter
import igraph as ig
import time
import scipy.sparse.linalg as sla

def stampa_info_doc(documents, triples, doc_id, text=False):
    """
    Dato il doc_id, visualizza i campi: one_sentence summary, Categoria, Range di Date.
    Poi visualizza le relazioni semantiche estrapolate dall'AI sul documento.
    Se il documento è 'HOUSE_OVERSIGHT_013343', allora non stampa il testo.
    """

    my_triples = triples[triples['doc_id'] == doc_id]
    my_document = documents[documents['doc_id'] == doc_id]

    # Safety check so it doesn't crash if the doc_id is misspelled
    if my_document.empty:
        print(f"\n⚠️ Document '{doc_id}' not found in the database.\n")
        return

    # ANSI Color Codes for a fancier terminal output
    BOLD = '\033[1m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'

    # The :=^80 centers the text and pads it with '=' up to exactly 80 characters
    print(f"\n{CYAN}{f' DOCUMENT ID: {doc_id} ':=^80}{RESET}\n")
    
    # --- METADATA & SUMMARY ---
    print(f"{BOLD}SUMMARY:{RESET}")
    print(f"{my_document['one_sentence_summary'].iloc[0]}\n")
    
    print(f"{BOLD}METADATA:{RESET}")
    print(f" • Category:   {my_document['category'].iloc[0]}")
    print(f" • Date Range: {my_document['date_range_earliest'].iloc[0]} to {my_document['date_range_latest'].iloc[0]}\n")
    
    # --- SEMANTIC RELATIONS ---
    print(f"{CYAN}{' PARSED RELATIONS ':-^80}{RESET}\n")
    print(f"Found {BOLD}{len(my_triples)}{RESET} semantic relations ({GREEN}Actor{RESET} → {BOLD}Action{RESET} → {MAGENTA}Target{RESET}):\n")
    
    for i, triple in enumerate(my_triples.itertuples(index=False), start=1):
        # Uses '.' as padding to separate triples cleanly
        print(f"{YELLOW}{f' Relation {i} ':.^80}{RESET}")
        
        # Color codes make parsing the main action instantly readable
        print(f" {BOLD}▶{RESET} {GREEN}{triple.actor}{RESET} {BOLD}{triple.action}{RESET} {MAGENTA}{triple.target}{RESET}")
        print(f"   {BOLD}Location:{RESET} {triple.location}")
        print(f"   {BOLD}Tags:{RESET}     {triple.triple_tags}")
        print(f"   {BOLD}Explicit:{RESET} {triple.explicit_topic}")
        print(f"   {BOLD}Implicit:{RESET} {triple.implicit_topic}\n")

    # --- FULL TEXT ---
    if text:
        print(f"{CYAN}{' FULL TEXT ':=^80}{RESET}\n")
        print(my_document['full_text'].iloc[0])
        print(f"\n{CYAN}{'='*80}{RESET}\n")

def save_igraph_to_neo4j(driver, g, node_attrs=None, edge_attrs=None):
    """
    Uploads a bipartite igraph to Neo4j with dynamic attributes.
    
    :param driver: Neo4j database driver
    :param g: igraph object
    :param node_attrs: list of strings (e.g., ['summary', 'date', 'sentiment'])
    :param edge_attrs: list of strings (e.g., ['action', 'original_edge_id', 'weight'])
    """
    start_all = time.time()

# ==========================================
    # 0. BUILD UNIQUE CONSTRAINTS (AND INDEXES)
    # ==========================================
    print("Ensuring database constraints and indexes are online...")
    with driver.session() as session:
        # This guarantees no duplicate names AND builds a high-speed index
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.name IS UNIQUE")
        
        # If your Neo4j version is older than 4.4, the syntax is:
        # session.run("CREATE CONSTRAINT ON (e:Entity) ASSERT e.name IS UNIQUE")
    
    # Ensure they are lists to avoid NoneType iteration errors
    node_attrs = node_attrs or []
    edge_attrs = edge_attrs or []

    # ==========================================
    # 1. NODES: DYNAMIC ATTRIBUTE MERGE 
    # ==========================================
    print(f"Preparing {g.vcount()} nodes...")
    nodes_by_label = {"Entity": [], "Document": []}
    
    for v in g.vs:
        v_attr = v.attributes()
        label = "Document" if v_attr.get('type') else "Entity"
        
        # Dynamically pack requested node properties
        props = {}
        for attr in node_attrs:
            val = v_attr.get(attr)
            # Only add if it exists (so Entities don't get 'summary: None')
            if val is not None: 
                props[attr] = str(val)
                
        nodes_by_label[label].append({
            "name": str(v_attr.get('name')),
            "properties": props
        })

    with driver.session() as session:
        for label, node_list in nodes_by_label.items():
            print(f"\nMerging {len(node_list)} {label} nodes...")
            for i in range(0, len(node_list), 5000):
                chunk = node_list[i:i + 5000]
                
                # SET n += row.properties dynamically adds everything in the dict!
                query = f"""
                UNWIND $batch AS row 
                MERGE (n:{label} {{name: row.name}})
                SET n += row.properties
                """
                session.run(query, batch=chunk)
                print(f"  > Nodes: {min(i+5000, len(node_list))}/{len(node_list)}")

    print(f"\nNodes finished in {time.time() - start_all:.1f}s")

    # ==========================================
    # 2. EDGES: DYNAMIC ATTRIBUTE BLAST
    # ==========================================
    print(f"\nPreparing {g.ecount()} edges...")
    
    buckets = {}
    for e in g.es:
        s_node, t_node = g.vs[e.source], g.vs[e.target]
        attrs = e.attributes()
        
        s_lab = "Document" if s_node['type'] else "Entity"
        t_lab = "Document" if t_node['type'] else "Entity"
        
        # Dynamically pack requested edge properties
        props = {}
        for attr in edge_attrs:
            val = attrs.get(attr)
            if val is not None:
                props[attr] = str(val)
        
        key = (s_lab, t_lab)
        if key not in buckets: 
            buckets[key] = []
            
        buckets[key].append({
            "s": str(s_node['name']),
            "t": str(t_node['name']),
            "properties": props
        })

    edge_start = time.time()
    total_edges = g.ecount()
    edges_done = 0
    
    with driver.session() as session:
        for (sl, tl), edge_list in buckets.items():
            print(f"\nBlasting {len(edge_list)} edges for {sl} -> {tl}...")
            
            for i in range(0, len(edge_list), 5000):
                chunk = edge_list[i:i + 5000]
                
                # SET r += row.properties automatically attaches your dynamic list
                query = f"""
                UNWIND $batch AS row
                MATCH (source:{sl} {{name: row.s}})
                MATCH (target:{tl} {{name: row.t}})
                CREATE (source)-[r:RELATION]->(target)
                SET r += row.properties
                """
                session.run(query, batch=chunk)
                
                edges_done += len(chunk)
                elapsed = time.time() - edge_start
                print(f"  > Edges: {edges_done}/{total_edges} ({elapsed:.1f}s)")

    print(f"\n\nTOTAL SUCCESS: Graph uploaded in {time.time() - start_all:.1f} seconds.")


def read_neo4j_to_igraph(driver):
    """
    Pulls all nodes and edges from Neo4j, unpacks their dynamic properties,
    and reconstructs the directed bipartite igraph object.
    """
    t0 = time.time()
    
    with driver.session() as session:
        # ==========================================
        # 1. PULL NODES & UNPACK PROPERTIES
        # ==========================================
        print("Downloading nodes from Neo4j...")
        node_query = """
        MATCH (n) 
        RETURN labels(n)[0] AS label, properties(n) AS props
        """
        node_records = session.run(node_query)
        
        nodes_data = []
        for record in node_records:
            row = record["props"]
            row["label"] = record["label"]
            nodes_data.append(row)
            
        nodes_df = pd.DataFrame(nodes_data)
        
        # igraph needs the boolean 'type' column for bipartite graphs
        nodes_df['type'] = nodes_df['label'] == 'Document'
        
        # ---> THE FIX: FORCE 'name' TO BE THE FIRST COLUMN <---
        # This is still inside the 'with' block indentation
        all_node_cols = list(nodes_df.columns)
        if 'name' in all_node_cols:
            all_node_cols.remove('name')
            nodes_df = nodes_df[['name'] + all_node_cols]
        
        print(f"  > Downloaded {len(nodes_df)} nodes.")

        # ==========================================
        # 2. PULL EDGES & UNPACK PROPERTIES
        # ==========================================
        print("Downloading edges from Neo4j...")
        edge_query = """
        MATCH (s)-[r]->(t)
        RETURN s.name AS source, t.name AS target, properties(r) AS props
        """
        edge_records = session.run(edge_query)
        
        edges_data = []
        for record in edge_records:
            row = record["props"]
            row["source"] = record["source"]
            row["target"] = record["target"]
            edges_data.append(row)
            
        edges_df = pd.DataFrame(edges_data)
        print(f"  > Downloaded {len(edges_df)} edges.")

    # ==========================================
    # 3. RECONSTRUCT THE IGRAPH
    # ==========================================
    # Notice we are OUTSIDE the 'with' block now. 
    # We hung up the phone with Neo4j and are just doing Python/igraph math.
    print("Stitching igraph object...")
    
    all_cols = list(edges_df.columns)
    all_cols.remove('source')
    all_cols.remove('target')
    ordered_cols = ['source', 'target'] + all_cols
    edges_df = edges_df[ordered_cols]
    
    g = ig.Graph.DataFrame(
        edges=edges_df,
        directed=True,
        vertices=nodes_df,
        use_vids=False 
    )
    
    print(f"\nSUCCESS: Graph reconstructed in {time.time() - t0:.1f} seconds.")
    return g


def compare_graphs(g1, g2, node_attrs=None, edge_attrs=None):
    """
    Validates two igraphs against each other, dynamically checking only 
    the specific node and edge attributes provided.
    """
    node_attrs = node_attrs or []
    edge_attrs = edge_attrs or []
    
    print(f"=== 1. CHECKING BASIC SIZE ===")
    v_match = g1.vcount() == g2.vcount()
    e_match = g1.ecount() == g2.ecount()
    
    print(f"Original:   {g1.vcount()} nodes, {g1.ecount()} edges")
    print(f"Downloaded: {g2.vcount()} nodes, {g2.ecount()} edges")
    print(f"Size Match? Nodes: {v_match} | Edges: {e_match}\n")

    # Helper function to ensure 'None', NaN, and empty strings are treated identically
    def clean_val(val):
        if val is None or pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
            return "None"
        return str(val)

    print(f"=== 2. CHECKING NODES (By Name + {node_attrs}) ===")
    def extract_nodes(g):
        node_signatures = set()
        for v in g.vs:
            name = clean_val(v.attributes().get('name'))
            
            # Dynamically grab the exact attributes you asked to check
            attrs = tuple(clean_val(v.attributes().get(attr)) for attr in node_attrs)
            
            # Pack name and attributes into a single tuple to hash
            node_signatures.add((name,) + attrs)
        return node_signatures
        
    nodes1 = extract_nodes(g1)
    nodes2 = extract_nodes(g2)
    
    missing_nodes = nodes1 - nodes2
    extra_nodes = nodes2 - nodes1
    
    if not missing_nodes and not extra_nodes:
        print("✅ Node sets and requested attributes are 100% identical.")
    else:
        print(f"❌ Mismatch! Missing {len(missing_nodes)} nodes, found {len(extra_nodes)} extra.")
        if missing_nodes:
            print("Example missing node signature:", list(missing_nodes)[0])

    print(f"\n=== 3. CHECKING EDGES (By Source, Target + {edge_attrs}) ===")
    def extract_edges(g):
        edge_signatures = set()
        for e in g.es:
            s_name = clean_val(g.vs[e.source]['name'])
            t_name = clean_val(g.vs[e.target]['name'])
            
            # Dynamically grab the exact attributes you asked to check
            attrs = tuple(clean_val(e.attributes().get(attr)) for attr in edge_attrs)
            
            # Pack source, target, and attributes into a single tuple
            edge_signatures.add((s_name, t_name) + attrs)
        return edge_signatures

    edges1 = extract_edges(g1)
    edges2 = extract_edges(g2)
    
    missing_edges = edges1 - edges2
    extra_edges = edges2 - edges1
    
    if not missing_edges and not extra_edges:
        print("✅ Edge sets and requested attributes are 100% identical.")
    else:
        print(f"❌ Mismatch! Missing {len(missing_edges)} edges, found {len(extra_edges)} extra.")
        if missing_edges:
            print("Example missing edge signature:", list(missing_edges)[0])



def compute_and_store_metrics(g):
    """
    Computes a wide array of node and edge metrics for a directed graph
    and stores them directly inside the igraph object as attributes.
    """
    print(f"Starting metrics computation for graph with {g.vcount()} nodes and {g.ecount()} edges...\n")
    total_start = time.time()

    # ==========================================
    # 1. NODE DEGREES
    # ==========================================
    t0 = time.time()
    g.vs["degree_all"] = g.degree(mode="all")
    g.vs["degree_in"] = g.degree(mode="in")
    g.vs["degree_out"] = g.degree(mode="out")
    print(f"[Time] Degrees (In/Out/All): {time.time() - t0:.2f} s")

    # ==========================================
    # 2. CENTRALITIES (The Heavy Lifters)
    # ==========================================
    t0 = time.time()
    g.vs["pagerank"] = g.pagerank(directed=True)
    print(f"[Time] PageRank: {time.time() - t0:.2f} s")

    t0 = time.time()
    # Warning: Betweenness can take a minute on 180k edges. 
    g.vs["betweenness"] = g.betweenness(directed=True)
    print(f"[Time] Node Betweenness: {time.time() - t0:.2f} s")

    t0 = time.time()
    g.vs["eigenvector"] = g.eigenvector_centrality(directed=True)
    print(f"[Time] Eigenvector Centrality: {time.time() - t0:.2f} s")

    # ==========================================
    # 3. HUBS & AUTHORITIES (HITS)
    # ==========================================
    t0 = time.time()
    
    # Check if the graph is strictly bipartite before running HITS
    if g.is_bipartite():
        print("Graph is bipartite. Computing HITS...")
        # Entities will naturally score high here
        g.vs["hub_score"] = g.hub_score()
        # Documents will naturally score high here
        g.vs["authority_score"] = g.authority_score()
        print(f"[Time] HITS (Hubs & Authorities): {time.time() - t0:.2f} s")
    else:
        print("Graph is NOT perfectly bipartite. Skipping HITS...")
        # Fill with None so your dataframe doesn't break later
        g.vs["hub_score"] = [None] * g.vcount()
        g.vs["authority_score"] = [None] * g.vcount()

    # ==========================================
    # 4. STRUCTURAL METRICS
    # ==========================================
    t0 = time.time()
    # Coreness (k-core decomposition): measures how deeply embedded a node is
    g.vs["coreness"] = g.coreness(mode="all")
    print(f"[Time] Coreness (k-core): {time.time() - t0:.2f} s")

    t0 = time.time()
    # Local Clustering Coefficient (transitivity). 
    # mode="zero" ensures nodes with degree < 2 get a score of 0 instead of NaN
    g.vs["clustering_coeff"] = g.transitivity_local_undirected(mode="zero")
    print(f"[Time] Local Clustering Coefficient: {time.time() - t0:.2f} s")

    # ==========================================
    # 5. EDGE METRICS
    # ==========================================
    t0 = time.time()
    g.es["edge_betweenness"] = g.edge_betweenness(directed=True)
    print(f"[Time] Edge Betweenness: {time.time() - t0:.2f} s")
    
    # ------------------------------------------
    print(f"\n✅ All metrics computed and stored in {time.time() - total_start:.1f} seconds total.")
    return g




def extract_main_component(g, warning_threshold=0.10):
    """
    Extracts the giant component but alerts you if the 2nd largest component 
    holds more than X% of the total nodes.
    """
    print(f"Analyzing components for graph with {g.vcount()} nodes...")
    
    # 1. Find all weakly connected components
    components = g.components(mode="weak")
    sizes = components.sizes()
    
    # Sort the component sizes from largest to smallest
    sorted_sizes = sorted(sizes, reverse=True)
    
    print(f"  > Largest component: {sorted_sizes[0]} nodes")
    
    # 2. The Safeguard Check
    if len(sorted_sizes) > 1:
        print(f"  > Second largest component: {sorted_sizes[1]} nodes")
        ratio = sorted_sizes[1] / g.vcount()
        
        if ratio > warning_threshold:
            print(f"⚠️ WARNING: The second component holds {ratio*100:.1f}% of your data!")
            print("You might want to extract and analyze it separately.")
            
    # 3. Extract and return the Giant Component (attributes are kept automatically)
    giant_g = components.giant()
    return giant_g




def compute_communities(g):
    """
    Runs Laplacian (Fiedler), Louvain, and Infomap.
    Stores cluster memberships as node attributes and modularity/gaps as graph attributes.
    """
    print(f"\n--- Starting Community Detection for {g.vcount()} nodes ---")
    total_start = time.time()

    #Why am I converting it to a directed graph: It is interesting to study the non-directed version of it
    #==========================================
    # 1. LAPLACIAN (Fiedler Vector & Spectral Gap)
    # ==========================================
    t0 = time.time()
    try:
        # Fiedler vector requires an undirected graph
        g_un = g.as_undirected(mode="collapse")
        
        # 1. Get the sparse Adjacency matrix (A)
        A = g_un.get_adjacency_sparse()
        
        # 2. Create the sparse Degree matrix (D)
        degrees = g_un.degree()
        D = sp.diags(degrees)
        
        # 3. Calculate the Laplacian (L = D - A)
        L = D - A
        
        # 4. Calculate the 2 smallest algebraic ('SA') eigenvalues/vectors
        # We use eigsh because the undirected Laplacian is symmetric
        eigenvalues, eigenvectors = sla.eigsh(L, k=2, which='SA')
        
        # eigenvalues[0] is ~0. eigenvalues[1] is the Spectral Gap.
        g["spectral_gap"] = float(eigenvalues[1])
        g.vs["fiedler_vector"] = eigenvectors[:, 1].tolist()
        
        print(f"[Time] Laplacian (Spectral Gap: {eigenvalues[1]:.5f}): {time.time() - t0:.2f} s")
    except Exception as e:
        print(f"[Time] Laplacian FAILED: {e}")


    # ==========================================
    # 1. LAPLACIAN (Fiedler Vector & Spectral Gap)
    # ==========================================
    t0 = time.time()
    try:
        L = g.get_laplacian(sparse=True)
        eigenvalues, eigenvectors = sla.eigsh(L, k=2, which='SM')
        
        g["spectral_gap"] = float(eigenvalues[1])
        g.vs["fiedler_vector"] = eigenvectors[:, 1].tolist()
        print(f"[Time] Laplacian (Spectral Gap: {eigenvalues[1]:.5f}): {time.time() - t0:.2f} s")
    except Exception as e:
        print(f"[Time] Laplacian FAILED: {e}")

    # ==========================================
    # 2. LOUVAIN (Requires Undirected Graph)
    # ==========================================
    t0 = time.time()
    g_undirected = g.as_undirected(mode="collapse")
    print(f"[Time] Graph undirected conversion (for Louvain): {time.time() - t0:.2f} s")
    
    t0 = time.time()
    louvain = g_undirected.community_multilevel()
    g.vs["louvain_cluster"] = louvain.membership
    g["louvain_modularity"] = louvain.modularity
    print(f"[Time] Louvain Community Detection: {time.time() - t0:.2f} s")

    # ==========================================
    # 3. INFOMAP (Works on Directed Graphs)
    # ==========================================
    t0 = time.time()
    # Infomap tracks 'flow', which is perfect for directed document/entity networks
    infomap = g.community_infomap()
    g.vs["infomap_cluster"] = infomap.membership
    g["infomap_modularity"] = infomap.modularity
    print(f"[Time] Infomap Community Detection: {time.time() - t0:.2f} s")

    print(f"✅ Community Detection complete in {time.time() - total_start:.1f} s total.")
    return g



def compute_global_statistics(g):
    """
    Computes graph-wide metrics like Density, Diameter, and Reciprocity,
    and stores them directly inside the igraph object as graph attributes.
    """
    print(f"\n--- Computing Global Graph Statistics ---")
    t_total = time.time()

    t0 = time.time()
    g["num_vertices"] = g.vcount()
    g["num_edges"] = g.ecount()
    print(f"[Time] Basic counts: {time.time() - t0:.2f} s")

    t0 = time.time()
    g["density"] = g.density()
    print(f"[Time] Density: {time.time() - t0:.2f} s")
    
    t0 = time.time()
    # Reciprocity: How many edges go both ways (A <-> B). 
    g["reciprocity"] = g.reciprocity() 
    print(f"[Time] Reciprocity: {time.time() - t0:.2f} s")



    t0 = time.time()
    print("Calculating Average Path Length (this may take a minute...)")
    # Removed 'unweighted=True'. igraph defaults to unweighted automatically!
    g["avg_path_length"] = g.average_path_length(directed=True)
    print(f"[Time] Average Path Length: {time.time() - t0:.2f} s")

    t0 = time.time()
    print("Calculating Diameter (this may take a minute...)")
    # Removed 'unweighted=True'.
    g["diameter"] = g.diameter(directed=True)
    print(f"[Time] Diameter: {time.time() - t0:.2f} s")


    print(f"✅ Global Statistics computed and stored in {time.time() - t_total:.1f} s total.")
    return g




def clean_communities_and_bisect(g, alpha = 0.1):
    """
    1. Binarizes the Laplacian Fiedler vector (1 for >= 0, 0 for < 0).
    2. Cleans Infomap communities by assigning small clusters to -1.
    3. Returns the updated graph and a formal igraph VertexClustering object.
    """


    # --- 1. LAPLACIAN SPECTRAL BISECTION (0 or 1) ---
    ones_count = 0
    zeros_count = 0
    min_size = alpha * g.vcount()
    print(f"Cleaning communities (min_size={min_size}) and applying bisection...")
    for v in g.vs:
        f_val = v.attributes().get("fiedler_vector")
        
        if f_val is not None:
            # 1 if >= 0, 0 if < 0
            binary_split = 1 if f_val >= 0 else 0
            v["laplacian_split"] = binary_split
            
            if binary_split == 1: ones_count += 1
            else: zeros_count += 1
        else:
            v["laplacian_split"] = None

    print(f"  > Laplacian Split: {ones_count} nodes (1) | {zeros_count} nodes (0)")

    # --- 2. REBUILDING THE INFOMAP OBJECT ---
    original_membership = g.vs["infomap_cluster"]
    
    # Count how many nodes are in each cluster
    cluster_counts = Counter(original_membership)
    
    cleaned_membership = []
    
    for cluster_id in original_membership:
        # If the cluster is big enough, keep its ID. Otherwise, throw it in the -1 bin.
        if cluster_counts[cluster_id] >= min_size:
            cleaned_membership.append(cluster_id)
        else:
            cleaned_membership.append(-1)
            
    # Store the cleaned list as a new node attribute for your Pandas dataframe
    g.vs["cleaned_infomap"] = cleaned_membership
    
    # Create the formal igraph VertexClustering object "in the same way it was passed"
    cleaned_infomap_obj = ig.VertexClustering(g, membership=cleaned_membership)
    
    valid_clusters = [cid for cid, count in cluster_counts.items() if count >= min_size]
    print(f"  > Infomap: Kept {len(valid_clusters)} major communities.")
    print(f"  > All other nodes assigned to noise cluster (-1).")

    return g, cleaned_infomap_obj
