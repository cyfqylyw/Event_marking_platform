import gradio as gr
import requests
import os
import json
from datetime import datetime
import shutil
import sqlite3

port = 5321
local_host = 'localhost'

USERNAME = 'tzw'
PASSWORD = 'lyw'
SAVE_PATH = '../data/files/'

db_name = '../data/dbs/mev.db'
usernames_passwords = [
    ("Leonardo", "583920"),
    ("Galileo", "174839"),
    ("Einstein", "839201"),
    ("Shakespeare", "482013"),
    ("Mozart", "320184"),
    ("Picasso", "951837"),
    ("Beethoven", "230947"),
    ("Darwin", "509283"),
    ("Newton", "748291"),
    ("Curie", "374829")
]
num_annotators = len(usernames_passwords)


# 这里提供了登录和获取标注数据的假设函数
def login(username, password):
    # 模拟登录流程
    if username == USERNAME and password == PASSWORD:
        return "管理员登陆成功！"
    else:
        return "管理员登录失败，请检查用户名和密码!"
    

def save_uploaded_file(username, password, file):
    if username == USERNAME and password == PASSWORD:
        if file is not None:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = os.path.basename(file.name)

            if not file_name.endswith('.json'):
                return "上传失败，请上传json格式文件", "未更新"
            
            file_save_path = os.path.join(SAVE_PATH, f'{current_time}_{file_name}')
            shutil.copy(file.name, file_save_path)
            upload_output_text = f"文件已保存到  {file_save_path}"

            # --------------------------------------------
            # 更新数据库
            # --------------------------------------------

            # 备份数据库
            os.rename('../data/dbs/mev.db', f'../data/dbs/replaced_{current_time}_mev.db')

            connection = sqlite3.connect(db_name)
            with connection:
                cursor = connection.cursor()
                # 获取所有表名
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()

                # 删除所有表
                for table in tables:
                    print(f"Deleting table {table[0]}")
                    cursor.execute(f"DROP TABLE {table[0]}")

                # 创建用户表，存储所有 num_annotators 个标注者的用户名和密码
                cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
                for user_id, (username, pswd) in enumerate(usernames_passwords):
                    cursor.execute("INSERT INTO users (id, username, password) VALUES (?, ?, ?)", (user_id, username, pswd))

                # 创建标注数据表
                cursor.execute("CREATE TABLE IF NOT EXISTS annotations (id TEXT PRIMARY KEY, user_id INTEGER, data TEXT, is_annotated BOOL, data_status TEXT, FOREIGN KEY(user_id) REFERENCES users(id))")

                with open(file_save_path, 'r') as file: 
                    # 将 file_save_path 读取到一个 list
                    dataset = json.load(file)
                    for data in dataset:
                        data_id = data['id']
                        user_id = data_id % num_annotators
                        is_annotated = 0
                        data_status = 'TODO'

                        cursor.execute("INSERT INTO annotations (id, user_id, data, is_annotated, data_status) VALUES (?, ?, ?, ?, ?)", (data_id, user_id, json.dumps(data), is_annotated, data_status))
                    cursor.execute(f"SELECT COUNT(*) FROM annotations")
                    rows_count = cursor.fetchone()[0]

                update_output_text = f"数据库和表创建成功，Number of annotations: {rows_count}"

            return upload_output_text, update_output_text
        
        return "未上传文件", "未更新"
    else:
        error = "管理员用户名和密码错误"
        return error, error


def download_output(username, password):
    if username == USERNAME and password == PASSWORD:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_name = os.path.join('../data/out/', f'{current_time}_output_dataset.json')

        connection = sqlite3.connect(db_name)
        with connection:
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM annotations;')
            outputs = cursor.fetchall()

            results = []
            for out in outputs:
                data_id = out[0]
                annotator_id = out[1]

                data = json.loads(out[2])
                is_annotated = out[3]
                data['is_annotated'] = is_annotated
                data_status = out[4]
                data['data_status'] = data_status
                results.append(data)

            with open(output_file_name, 'w') as json_file:
                json.dump(results, json_file, indent=4)

        return output_file_name, "导出成功"
    else:
        return None, "管理员用户名和密码错误"


with gr.Blocks() as demo:
    gr.Markdown('# Welcome!')
    # 登录区域
    with gr.Row():
        username_input = gr.Textbox(label="Username")
        password_input = gr.Textbox(label="Password", type="password")
    with gr.Row():
        login_btn = gr.Button("Login")
        login_status = gr.Textbox(label="Login Status")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown('# 上传文件，重置数据库中所有data_id')
            upload_file = gr.File(label="上传json格式文件")
            upload_button = gr.Button("上传文件并更新数据库")
            upload_output_text = gr.Textbox(label="文件上传结果")
            update_output_text = gr.Textbox(label="数据库更新结果")
        with gr.Column(scale=1):
            gr.Markdown('# 下载当前所有标注结果')
            download_button = gr.Button("下载文件")
            download_file = gr.File(label="下载文件")
            download_output_text = gr.Textbox(label="文件下载结果")


    # 设置按钮点击后的动作
    login_btn.click(fn=login, 
                    inputs=[username_input, password_input], 
                    outputs=[login_status])
    
    upload_button.click(fn=save_uploaded_file, 
                        inputs=[username_input, password_input, upload_file], 
                        outputs=[upload_output_text, update_output_text]
                        )

    download_button.click(fn=download_output,
                          inputs=[username_input, password_input],
                          outputs=[download_file, download_output_text]
                          )


# demo.launch(server_name='0.0.0.0', server_port=5320, root_path='/event_admin')
demo.launch(server_name='127.0.0.1', server_port=5320, root_path='/event_admin')
