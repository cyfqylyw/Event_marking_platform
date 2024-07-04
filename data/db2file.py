import sqlite3
import json
import pdb
import argparse

db_name = '../data/dbs/mev.db'
output_file_name = '../data/out/output_dataset.json'

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
        results.append(data)

    with open(output_file_name, 'w') as json_file:
        json.dump(results, json_file, indent=4)
