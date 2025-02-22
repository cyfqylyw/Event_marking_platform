import networkx as nx
import matplotlib.pyplot as plt


def draw_fig3(raw_data, filename):
    nodes = raw_data['nodes']
    edges = raw_data['edges']
    
    G = nx.DiGraph()
    
    # Add nodes
    for node_id, attributes in nodes.items():
        G.add_node(node_id, **attributes)

    # Add edges
    for head, rel, tail in edges:
        G.add_edge(head, tail, rel=rel[0])

    # pos = nx.spring_layout(G)
    pos = nx.drawing.nx_pydot.graphviz_layout(G, root=0, prog='dot')
    branch_colors = {}
    colors = ['skyblue', 'lightgreen', 'salmon', 'gold', 'violet', 'lightgrey', 'orange', 'cyan']
    for node, data in G.nodes(data=True):
        branch = data.get('branch', None)
        if branch not in branch_colors:
            if colors:
                branch_colors[branch] = colors.pop(0)
            else:
                colors = ['skyblue', 'lightgreen', 'salmon', 'gold', 'violet', 'lightgrey', 'orange', 'cyan']
                branch_colors[branch] = colors.pop(0)

    node_colors = [branch_colors.get(data.get('branch', None), 'gray') for _, data in G.nodes(data=True)]
    node_labels = {node: node for node, data in G.nodes(data=True)}
    
    # Use 'Agg' backend to avoid GUI issues
    plt.switch_backend('Agg')
    
    fig, ax = plt.subplots(figsize=(5, 6))  # 可以调整图的大小
    ax.axis('off')
    
    # Draw edges normally
    nx.draw_networkx_edges(G, pos, edge_color='k', arrows=True, arrowstyle='->', arrowsize=20)
    # Draw all nodes initially
    nx.draw_networkx_nodes(G, pos, node_size=600, node_color=node_colors)

    
    # Select nodes with 'is_observed' attribute set to True and draw with bold outline
    observed_nodes = [node for node, data in G.nodes(data=True) if data.get('is_observed') == True]
    if observed_nodes:
        observed_node_colors = [branch_colors.get(G.nodes[node].get('branch', None), 'gray') for node in observed_nodes]
        nx.draw_networkx_nodes(G, pos, nodelist=observed_nodes, node_size=600, node_color=observed_node_colors,
                               edgecolors='black', linewidths=1)
    
    # Select nodes with 'type' attribute set to 'target' and draw with bold outline
    target_nodes = [node for node, data in G.nodes(data=True) if data.get('type') == 'target']
    if target_nodes:
        target_node_colors = [branch_colors.get(G.nodes[node].get('branch', None), 'gray') for node in target_nodes]
        nx.draw_networkx_nodes(G, pos, nodelist=target_nodes, node_size=600, node_color=target_node_colors,
                               edgecolors='red', linewidths=3)

    # Add dashed circles for unobserved nodes
    # for node, data in G.nodes(data=True):
    #     if not data.get('is_observed', True):  # for unobserved nodes
    #         print(pos[node])
    #         if node in pos:
    #             circle = plt.Circle(pos[node], radius=0.1, edgecolor='black', facecolor='none', linestyle='--', linewidth=2)
    #             ax.add_artist(circle)

    # Draw node labels
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=12)

    plt.tight_layout()  # Adjust layout to prevent clipping of node labels etc
    plt.savefig(filename, format="PNG")
    plt.close()
