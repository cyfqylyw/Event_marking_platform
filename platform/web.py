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
    return data_id, nodes, df_nodes_attributes, df_nodes_attributes_not_show, df_nodes_events, df_edges, direction, topic, img_path, is_annotated


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


with gr.Blocks() as demo:
    gr.Markdown('# Welcome!')
    # 登录区域
    with gr.Row():
        username_input = gr.Textbox(label="Username")
        password_input = gr.Textbox(label="Password", type="password")
    with gr.Row():
        login_btn = gr.Button("Login")
        login_status = gr.Textbox(label="Login Status")

    user_id = gr.Textbox(visible=False)
    data_id = gr.Textbox(visible=False)

    # 选择 data_id
    select_button = gr.Radio([], label='Choose your data')

    gr.Markdown('# Sample meta information (DO NOT CHANGE)')
    topic_display = gr.Textbox(label='Topic')
    direction_display = gr.Textbox(label='Direction')
    save_status = gr.Textbox(label='Save status')

    
    gr.Markdown('# Graph meta information')
    with gr.Row():
        with gr.Column(scale=10):
            gr.Markdown('## Node attributes')
            df_nodes_attributes = gr.Dataframe(interactive=True)
            df_nodes_attributes_not_show = gr.DataFrame(visible=False)
        with gr.Column(scale=1):
            gr.Markdown('## Edges')
            df_edges_display = gr.Dataframe(interactive=True)

    img_path = gr.Textbox(visible=False)
    nodes_display = gr.Textbox(visible=False)
    # edges_display = gr.Textbox(visible=False)

    with gr.Row():
        with gr.Column(scale=5):
            gr.Markdown('# Graph')
            gr.Markdown('## 如果觉得图不容易看，可以点击reload来重新绘图')
            image_display = gr.Image(label='Graph display') # 显示图片
        with gr.Column(scale=7):
            gr.Markdown('# Node event content')
            df_nodes_events = gr.Dataframe(interactive=True)
    

    reload_information_btn = gr.Button("Reload (放弃当前所有修改，回退到上一次保存的状态)")
    save_annotation_btn = gr.Button("Submit (根据已有修改更新数据库，不可逆)")


    # 设置按钮点击后的动作
    login_btn.click(fn=process_login_and_fetch_data_ids, 
                    inputs=[username_input, password_input], 
                    outputs=[user_id, select_button, login_status])
    
    select_button.change(fn=prepare_data,
                         inputs=[user_id, select_button],
                         outputs=[data_id, nodes_display, df_nodes_attributes, df_nodes_attributes_not_show,df_nodes_events, df_edges_display, direction_display, topic_display, image_display, save_status]
                         )
    
    
    reload_information_btn.click(fn=prepare_data,
                                 inputs=[user_id, select_button],
                                 outputs=[data_id, nodes_display, df_nodes_attributes, df_nodes_attributes_not_show,df_nodes_events, df_edges_display, direction_display, topic_display, image_display, save_status]
                                )

    save_annotation_btn.click(fn=save_annotations,
                              inputs=[user_id, data_id, df_nodes_attributes, df_nodes_attributes_not_show, df_nodes_events, df_edges_display, direction_display, topic_display],
                              outputs=[data_id, nodes_display, df_nodes_attributes, df_nodes_attributes_not_show,df_nodes_events, df_edges_display, direction_display, topic_display, image_display, save_status])



# demo.launch(server_name='0.0.0.0', server_port=5322)
demo.launch(server_name='127.0.0.1', server_port=5322)
