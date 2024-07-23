import gradio as gr
import requests
from PIL import Image
import json
import pandas as pd

port = 5321
local_host = 'localhost'


# 这里提供了登录和获取标注数据的假设函数
def login(username, password):
    # 模拟登录流程
    response = requests.post(f'http://{local_host}:{port}/login', json={"username": username, "password": password})
    if response.status_code == 200:
        return response.json()['user_id'], "登陆成功！"
    else:
        return None, "登录失败，请检查用户名和密码!"


def search_data_ids(user_id):
    response = requests.post(f'http://{local_host}:{port}/search_data_ids', json={'user_id': user_id})
    data_ids = response.json()['data_ids']
    return data_ids


# 第一个按钮：login 按钮
def process_login_and_fetch_data_ids(username, password):
    user_id, msg = login(username, password)
    if user_id is not None:
        data_ids = search_data_ids(user_id)
        if data_ids:
            return user_id, gr.Radio(choices=data_ids, label='Choose your data'), msg
        else:
            return user_id, None, "No data_id found for this user!"
    else:
        return None, None, "Login failed!"


def prepare_data(user_id, data_id):
    response = requests.post(f'http://{local_host}:{port}/read_data', json={'user_id': user_id, 'data_id': data_id})
    response = response.json()
    data_id = response['data_id']
    nodes = response['nodes']
    nodes_attributes = response['nodes_attributes']
    nodes_events = response['nodes_events']
    df_nodes_attributes = pd.DataFrame(nodes_attributes, columns=['node_id', 'branch', 'is_break', 'is_observed', 'type'])
    df_nodes_attributes_not_show = pd.DataFrame(nodes_attributes, columns=['can_break', 'prev_nodes'])
    df_nodes_events = pd.DataFrame(nodes_events, columns=['node_id', 'event'])

    edges = response['edges']
    df_edges = pd.DataFrame(edges, columns=['source', 'target'])

    direction = response['direction']
    topic = response['topic']
    img_path = response['img_path']
    is_annotated = 'Annotated' if response['is_annotated'] else 'TODO'
    data_status = response['data_status']
    return data_id, nodes, df_nodes_attributes, df_nodes_attributes_not_show, df_nodes_events, df_edges, direction, topic, img_path, is_annotated, data_status


def save_annotations(user_id, data_id, df_nodes_attributes, df_nodes_attributes_not_show, df_nodes_events, df_edges_display, direction_display, topic_display):
    df_edges_display = df_edges_display.to_dict()
    df_nodes_attributes = df_nodes_attributes.to_dict()
    df_nodes_attributes_not_show = df_nodes_attributes_not_show.to_dict()
    df_nodes_events = df_nodes_events.to_dict()

    to_save = {
            'user_id': user_id,
            'id': data_id,
            'direction': direction_display,
            'topic': topic_display,
            'df_edges_display': df_edges_display,
            'df_nodes_events': df_nodes_events,
            'df_nodes_attributes': df_nodes_attributes,
            'df_nodes_attributes_not_show': df_nodes_attributes_not_show
            }
    response = requests.post(f'http://{local_host}:{port}/save_data', json=to_save)
    return prepare_data(user_id, data_id)


def set_invalid_func(user_id, data_id):
    to_save = {
        'user_id': user_id,
        'id': data_id
    }
    response = requests.post(f'http://{local_host}:{port}/set_invalid', json=to_save)
    return prepare_data(user_id, data_id) 



with gr.Blocks() as demo:
    gr.Markdown('# Step 1: Login 登陆')
    # 登录区域
    with gr.Row():
        # CHANGE 0715
        username_input = gr.Textbox(label="Username", value="Leonardo")
        password_input = gr.Textbox(label="Password", type="password", value="583920")
    with gr.Row():
        login_btn = gr.Button("Login")
        login_status = gr.Textbox(label="Login Status")

    user_id = gr.Textbox(visible=False)
    data_id = gr.Textbox(visible=False)


    gr.Markdown('# Step 2.1: Choose data 选择数据')
    # 选择 data_id
    select_button = gr.Radio([], label='Choose your data')

    gr.Markdown('# Step 2.2: Meta information (DO NOT CHANGE)  查看元信息（无需标注）')
    topic_display = gr.Textbox(label='Topic')
    direction_display = gr.Textbox(label='Direction (cause / result)')
    save_status = gr.Textbox(label='Save status (TODO / Annotated)')
    data_status = gr.Textbox(label='Data status (TODO / Valid / Invalid)')

    
    gr.Markdown('# Step 3: Graph information 图的点和边信息（需要标注）')
    with gr.Row():
        with gr.Column(scale=10):
            gr.Markdown('## Node attributes 节点属性')
            df_nodes_attributes = gr.Dataframe(interactive=True)
            df_nodes_attributes_not_show = gr.DataFrame(visible=False)
        with gr.Column(scale=1):
            gr.Markdown('## Edges 边 （关系在2.2 direction中）')
            df_edges_display = gr.Dataframe(interactive=True)

    img_path = gr.Textbox(visible=False)
    nodes_display = gr.Textbox(visible=False)
    # edges_display = gr.Textbox(visible=False)

    gr.Markdown('# Step 4: Event information 事件信息（需要标注）')
    with gr.Row():
        with gr.Column(scale=5):
            gr.Markdown('# Graph 简单图示（无需标注）')
            gr.Markdown('## 如果觉得图不容易看，可以点击reload来重新绘图')
            image_display = gr.Image(label='Graph display') # 显示图片
        with gr.Column(scale=7):
            gr.Markdown('# Node event content')
            df_nodes_events = gr.Dataframe(interactive=True)
    

    reload_information_btn = gr.Button("Reload (放弃当前所有修改，回退到上一次保存的状态)")
    set_invalid_btn = gr.Button("Set Invalid (由于数据质量过低，完全无法标注，将其标记为invalid状态)")
    save_annotation_btn = gr.Button("Submit (根据已有修改/标注信息来更新数据库，不可回退)")



    # 设置按钮点击后的动作
    login_btn.click(fn=process_login_and_fetch_data_ids, 
                    inputs=[username_input, password_input], 
                    outputs=[user_id, select_button, login_status])
    
    select_button.change(fn=prepare_data,
                         inputs=[user_id, select_button],
                         outputs=[data_id, nodes_display, df_nodes_attributes, df_nodes_attributes_not_show,df_nodes_events, df_edges_display, direction_display, topic_display, image_display, save_status, data_status]
                         )
    
    
    reload_information_btn.click(fn=prepare_data,
                                 inputs=[user_id, select_button],
                                 outputs=[data_id, nodes_display, df_nodes_attributes, df_nodes_attributes_not_show,df_nodes_events, df_edges_display, direction_display, topic_display, image_display, save_status, data_status]
                                )

    save_annotation_btn.click(fn=save_annotations,
                              inputs=[user_id, data_id, df_nodes_attributes, df_nodes_attributes_not_show, df_nodes_events, df_edges_display, direction_display, topic_display],
                              outputs=[data_id, nodes_display, df_nodes_attributes, df_nodes_attributes_not_show,df_nodes_events, df_edges_display, direction_display, topic_display, image_display, save_status, data_status])
    
    set_invalid_btn.click(fn=set_invalid_func,
                          inputs=[user_id, data_id],
                          outputs=[data_id, nodes_display, df_nodes_attributes, df_nodes_attributes_not_show,df_nodes_events, df_edges_display, direction_display, topic_display, image_display, save_status, data_status])



# demo.launch(server_name='0.0.0.0', server_port=5322, root_path='/event')
demo.launch(server_name='127.0.0.1', server_port=5322, root_path='/event')
