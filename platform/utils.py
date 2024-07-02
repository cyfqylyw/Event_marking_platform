import networkx as nx
import matplotlib.pyplot as plt


def draw_fig2(data, file):
    nodes = data['nodes']
    edges = data['edges']
    
    G = nx.DiGraph()
    
    # Add nodes
    for node_id, attributes in nodes.items():
        G.add_node(node_id, **attributes)

    # Add edges
    for head, rel, tail in edges:
        G.add_edge(head, tail, rel=rel[0])
    
    # Color map for nodes
    color_map = {}
    for node_id, attributes in nodes.items():
        if 'type' not in attributes.keys():
            color_map[node_id] = 'lightgreen'
        elif attributes['type'] == 'root':
            color_map[node_id] = 'lightcoral'
        elif attributes['type'] == 'target':
            color_map[node_id] = 'lightblue'
        else:
            color_map[node_id] = 'lightgreen'
    node_colors = [color_map.get(node, 'black') for node in G.nodes()]
    
    # Draw the graph
    plt.switch_backend('Agg')
    fig, ax = plt.subplots(figsize=(20, 10))
    ax.axis('off')
    
    pos = nx.spring_layout(G)
    
    # Edge labels
    edge_labels = {edge: G.edges[edge]['rel'] for edge in G.edges()}
    
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='black', arrowsize=20)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=16, font_weight='bold')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=16)
    
    # Save the figure
    plt.savefig(file, format="PNG")
    plt.close(fig)


def draw_fig3(raw_data, filename):
    print(raw_data)
    nodes = raw_data['nodes']
    edges = raw_data['edges']
    
    G = nx.DiGraph()
    
    # Add nodes
    for node_id, attributes in nodes.items():
        G.add_node(node_id, **attributes)

    # Add edges
    for head, rel, tail in edges:
        G.add_edge(head, tail, rel=rel[0])

    pos = nx.spring_layout(G)
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
    
    fig, ax = plt.subplots(figsize=(20, 10))  # 可以调整图的大小
    ax.axis('off')
    
    # Draw edges normally
    nx.draw_networkx_edges(G, pos, edge_color='k', arrows=True, arrowstyle='->', arrowsize=10)
    # Draw all nodes initially
    nx.draw_networkx_nodes(G, pos, node_size=600, node_color=node_colors)

    # Select nodes with 'type' attribute set to 'target' and draw with bold outline
    target_nodes = [node for node, data in G.nodes(data=True) if data.get('type') == 'target']
    if target_nodes:
        target_node_colors = [branch_colors.get(G.nodes[node].get('branch', None), 'gray') for node in target_nodes]
        nx.draw_networkx_nodes(G, pos, nodelist=target_nodes, node_size=600, node_color=target_node_colors,
                               edgecolors='black', linewidths=3)

    # Add dashed circles for unobserved nodes
    for node, data in G.nodes(data=True):
        if not data.get('is_observed', True):  # for unobserved nodes
            circle = plt.Circle(pos[node], radius=0.05, edgecolor='black', facecolor='none', linestyle='--', linewidth=2)
            ax.add_artist(circle)

    # Draw node labels
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=12)

    plt.tight_layout()  # Adjust layout to prevent clipping of node labels etc
    plt.savefig(filename, format="PNG")
    plt.close()


def draw_fig(data, file):
    G = nx.DiGraph()
    for head, rel, tail in [[data['e0'], data['rel'], data['e1']]] + data['context_tpl']:
        G.add_edge(head, tail, rel=rel)

    e0 = data['e0']
    e1 = data['e1']
    path = [e0, e1]
    context_nodes = data['context_nodes']
    nodes = set(path + context_nodes)
    # descriptions = [f"[{n}] -- {data['instances'][n]}" for n in nodes]
    # negatives = data['negative']
    # # negatives = {k: v for k, v in data['negative'].items() if k in data['negative_chosen']}
    # negatives = [f'[{k}] -- {v}' for k, v in negatives.items() if k not in nodes]
    
    subG = G.subgraph(nodes)

    color_map = {path[0]: 'lightcoral', path[-1]: 'lightblue'}
    color_map.update({n: 'lightgreen' for n in context_nodes})
    node_colors = [color_map.get(node, 'black') for node in subG.nodes()]

    # 绘制子图，可以调整edge_color和width来突出显示边
    fig, ax = plt.subplots(figsize=(20, 10))  # 可以调整图的大小
    ax.axis('off')

    pos = nx.spring_layout(subG)  # 获取节点的位置布局

    # 获取子图的边标签
    sub_edge_labels = {edge: subG.edges[edge]['rel'] for edge in subG.edges()}
    # 绘制边标签
    nx.draw_networkx_nodes(subG, pos, ax=ax, node_color=node_colors)  # 增大结点
    nx.draw_networkx_edges(subG, pos, ax=ax, edge_color='black', arrowsize=20)
    nx.draw_networkx_labels(subG, pos, ax=ax, font_size=16, font_weight='bold')
    nx.draw_networkx_edge_labels(subG, pos, edge_labels=sub_edge_labels, font_size=16)

    # # 计算文本的垂直位置
    # step_size = 1.0 / (max(len(descriptions), len(negatives)) + 1)

    # # 在图的右侧添加描述
    # for i, desc in enumerate(descriptions):
    #     ax.text(0.6, 1.2 - (i + 1) * 0.2, s=textwrap.fill(desc, width=80), horizontalalignment='left', verticalalignment='center', fontsize=10, transform=ax.transAxes)
    #
    # # 在图的左侧添加描述
    # for i, desc in enumerate(negatives):
    #     ax.text(-0.2, 1.2 - (i + 1) * 0.1, s=textwrap.fill(desc, width=100), horizontalalignment='left', verticalalignment='center', fontsize=10, transform=ax.transAxes)
    #
    # # 调整子图边距以适应两侧的描述文本
    # fig.subplots_adjust(left=0.15, right=0.85)
        
    # 保存绘制的子图到文件
    plt.savefig(file, format="PNG")  # 保存为PNG文件
