from flask import Flask, request, jsonify, make_response
import sqlite3
import json
from utils import draw_fig3

app = Flask(__name__)

db_name = "../data/dbs/mev.db"
temp_img_prefix = "temp_img/"


def search_by_userid_and_dataid(user_id, data_id):
    # search data
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        # CHANGE 0715
        # f"SELECT data, is_annotated, data_status FROM annotations WHERE user_id={user_id} AND id='{data_id}'"
        f"SELECT data, is_annotated, data_status FROM annotations WHERE id='{data_id}'"
    )
    connection.commit()
    outputs = cursor.fetchall()[0]
    data = json.loads(outputs[0])
    is_annotated = outputs[1]
    data_status = outputs[2]
    connection.close()
    return data, is_annotated, data_status


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data["username"]
    password = data["password"]

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username = ? and password = ?;",
        (username, password),
    )
    connection.commit()
    user_id = cursor.fetchall()[0][0]
    connection.close()

    return jsonify({"message": "success", "user_id": user_id}), 200


@app.route("/search_data_ids", methods=["POST"])
def search_data_ids():
    data = request.json
    user_id = data["user_id"]

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()

    # CHANGE 0715
    # cursor.execute(f"SELECT id FROM annotations WHERE user_id={user_id}")
    cursor.execute(f"SELECT id FROM annotations")
    connection.commit()

    data_ids = [d[0] for d in cursor.fetchall()]
    connection.close()

    return jsonify({"message": "success", "data_ids": data_ids}), 200


@app.route("/read_data", methods=["POST"])
def read_data():
    inputs = request.json
    user_id = inputs["user_id"]
    data_id = inputs["data_id"]

    data, is_annotated, data_status = search_by_userid_and_dataid(user_id, data_id)

    # id
    data_id = data["id"]

    # save temp fig
    img_path = temp_img_prefix + user_id + "+" + str(data_id) + ".png"
    draw_fig3(data, img_path)

    # triple
    data_id = data["id"]

    nodes = data["nodes"]
    nodes_attributes = [
        {**{"node_id": node_id}, **{k: v for k, v in node.items() if k != "event"}}
        for node_id, node in nodes.items()
    ]
    nodes_events = [(node_id, node["event"]) for node_id, node in nodes.items()]

    edges = data["edges"]
    formatted_edges = [[edge[0], edge[2]] for edge in edges]

    direction = data["direction"]
    topic = data["topic"] # eval(data["topic"]) if type(data["topic"]) == type('aa') else data['topic']

    return (
        jsonify(
            {
                "message": "成功",
                "data_id": data_id,
                "nodes": nodes,
                "nodes_attributes": nodes_attributes,
                "nodes_events": nodes_events,
                "edges": formatted_edges,
                "direction": direction,
                "topic": topic,
                "img_path": img_path,
                "is_annotated": is_annotated,
                "data_status": data_status
            }
        ),
        200,
    )


@app.route("/save_data", methods=["POST"])
def save_data():
    inputs = request.json

    user_id = inputs["user_id"]
    data_id = inputs["id"]
    direction = inputs["direction"]
    topic = inputs["topic"]

    df_edges_dict = inputs["df_edges_display"]
    edges_lst = []
    for x, y in zip(df_edges_dict["source"].values(), df_edges_dict["target"].values()):
        edges_lst.append([x, direction, y])

    df_nodes_attributes = inputs["df_nodes_attributes"]
    df_nodes_attributes_not_show = inputs["df_nodes_attributes_not_show"]
    df_nodes_events = inputs["df_nodes_events"]
    nodes_dict = {}
    for node_id in df_nodes_attributes["node_id"].values():
        nodes_dict[node_id] = {
            "event": df_nodes_events["event"][node_id],
            "prev_nodes": df_nodes_attributes_not_show["prev_nodes"][node_id],
            "is_break": df_nodes_attributes["is_break"][node_id],
            "is_observed": df_nodes_attributes["is_observed"][node_id],
            "branch": df_nodes_attributes["branch"][node_id],
            "can_break": df_nodes_attributes_not_show["can_break"][node_id],
            "type": df_nodes_attributes["type"][node_id],
        }

    # dict_keys(['id', 'nodes', 'edges', 'direction', 'topic'])
    data = {}
    data["id"] = data_id
    data["nodes"] = nodes_dict
    data["edges"] = edges_lst
    data["direction"] = direction
    data["topic"] = topic

    data_str = json.dumps(data)
    is_annotated = 1
    data_status = "Valid"
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    # CHANGE 0715
    # sql_update_query = "UPDATE annotations SET data = ?, is_annotated = ?, data_status = ? WHERE user_id = ? AND id = ?;"
    # params = (data_str, is_annotated, data_status, user_id, data_id)
    sql_update_query = "UPDATE annotations SET data = ?, is_annotated = ?, data_status = ? WHERE id = ?;"
    params = (data_str, is_annotated, data_status, data_id)

    cursor.execute(sql_update_query, params)
    connection.commit()
    connection.close()
    return jsonify({"message": "成功", "is_annotated": is_annotated}), 200


@app.route("/set_invalid", methods=["POST"])
def set_invalid():
    inputs = request.json

    user_id = inputs["user_id"]
    data_id = inputs["id"]

    is_annotated = 1
    data_status = "Invalid"

    data, _, _ = search_by_userid_and_dataid(user_id, data_id)
    data_str = json.dumps(data)

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    # CHANGE 0715
    # sql_update_query = "UPDATE annotations SET data = ?, is_annotated = ?, data_status = ? WHERE user_id = ? AND id = ?;"
    # params = (data_str, is_annotated, data_status, user_id, data_id)
    sql_update_query = "UPDATE annotations SET data = ?, is_annotated = ?, data_status = ? WHERE id = ?;"
    params = (data_str, is_annotated, data_status, data_id)

    cursor.execute(sql_update_query, params)
    connection.commit()
    connection.close()
    return jsonify({"message": "成功", "is_annotated": is_annotated, "data_status": data_status}), 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5321, debug=True)
    # app.run(host="127.0.0.1", port=5321, debug=True)
