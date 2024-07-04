import json
import pdb
import random
import sqlite3

db_name = '../data/dbs/mev.db'
file_name = '../data/files/dataset_0625_30.json'


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

    connection.commit()

    # 创建用户表，存储所有 num_annotators 个标注者的用户名和密码
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    for user_id, (username, pswd) in enumerate(usernames_passwords):
        cursor.execute("INSERT INTO users (id, username, password) VALUES (?, ?, ?)", (user_id, username, pswd))
    
    # 创建标注数据表
    cursor.execute("CREATE TABLE IF NOT EXISTS annotations (id TEXT PRIMARY KEY, user_id INTEGER, data TEXT, is_annotated BOOL, FOREIGN KEY(user_id) REFERENCES users(id))")

    with open(file_name, 'r') as file: 
        # 将file_name读取到一个list
        dataset = json.load(file)

        # print(dataset[0].keys())  # dict_keys(['id', 'nodes', 'edges', 'direction', 'topic'])
    
        for data in dataset:
            data_id = data['id']
            user_id = data_id % num_annotators
            is_annotated = 0

            # nodes = data['nodes']
            # edges = data['edges']
            # direction = data['direction']
            # topic = data['topic']
            
            cursor.execute("INSERT INTO annotations (id, user_id, data, is_annotated) VALUES (?, ?, ?, ?)", (data_id, user_id, json.dumps(data), is_annotated))
        
        cursor.execute(f"SELECT COUNT(*) FROM annotations")
        rows_count = cursor.fetchone()[0]

    print(f"{file_name} to {db_name} 数据库和表创建成功！")
    print(f'Number of annotations: {rows_count}')
    


