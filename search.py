#!/usr/bin/env python3
from elasticsearch import Elasticsearch
import subprocess
import sys

from collections import namedtuple
import argparse

parser = argparse.ArgumentParser(description='Search documents.')
parser.add_argument('query', nargs='+', type=str, help='The search term')
parser.add_argument('-a', '--author', nargs='+', type=str, help='Authors name')
args = parser.parse_args()

Color = namedtuple('Color', ['purple', 'cyan', 'darkcyan', 'blue', 'green',
                             'yellow', 'red', 'bold', 'underline', 'end'],
                   defaults=['\033[95m', '\033[96m', '\033[36m', '\033[94m',
                             '\033[92m', '\033[93m', '\033[91m', '\033[1m',
                             '\033[4m', '\033[0m'])
color = Color()
# PURPLE    = '\033[95m'
# CYAN      = '\033[96m'
# DARKCYAN  = '\033[36m'
# BLUE      = '\033[94m'
# GREEN     = '\033[92m'
# YELLOW    = '\033[93m'
# RED       = '\033[91m'
# BOLD      = '\033[1m'
# UNDERLINE = '\033[4m'
# END       = '\033[0m'

es = Elasticsearch(['localhost'])

def print_res(result, index=None):
    if index is not None:
        print(i, color.bold+color.blue+result['title']+color.end)
        if result['description']:
            print("  Description:\t", result['description'])
        print(" ", result['highlight'])
        print("  Path: ", result['path'])
    else:
        print("Title:\t\t", result['title'])
        if result['description']:
            print("Description:\t", result['description'])
        print(result['highlight'])
        print("Path: ", result['path'])


user_search = None
if len(args.query) > 1:
    user_search = ' '.join(args.query)
else:
    user_search = args.query[0]

req_body = {
    "query": {
        "multi_match" : {
            "query" : user_search,
            "fields" : ["content", "title", "author"],
            "fuzziness" : "AUTO"
        }
    },
    "sort": {
        "_score": {"order": "desc"}
    },
    "highlight": {
        "pre_tags"  : [color.bold+color.blue],
        "post_tags" : [color.end],
        "order"     : "score",
        "number_of_fragments" : 1,
        "fields": {
            "content": {}
        }
    },
    "_source" : ['file.filename', 'path.real', 'meta.title', 'meta.raw.description']
}

res2 = es.search(index="test", body=req_body, _source=['file.filename', 'path.real', 'meta.title', 'meta.raw.description'])

# import urllib.request
# import json

# # decoder = json.JSONDecoder(strict=False)
# body = json.dumps(req_body).encode('utf-8')
# req = urllib.request.Request("http://localhost:9200/test/_search", data=body,
#               headers={"Content-Type" : "application/json"}, method="GET")

# with urllib.request.urlopen(req) as x:
#     res_string = x.read()
#     res_json = json.loads(res_string, strict=False)
#     print(x.status)

# res2 = res_json


# parse results
interesting = []
for item in res2['hits']['hits']:
    source = item['_source']
    meta = source.get('meta')

    title     = 'No title found'
    descr     = None
    os_path   = None
    highlight = None
    if meta is not None:
        title = meta.get('title')
        if meta.get('raw') is not None:
            descr = meta.get('raw').get('description')
    
    path  = source.get('path')    
    if path is not None:
        os_path = path.get('real')
    highlight = str(item['highlight']['content'][0]).replace('\n', '')
    temp = {
        'id' :          item['_id'],
        'title' :       title,
        'description' : descr,
        'path' :        os_path,
        'highlight' :   highlight
    }
    interesting.append(temp)
    
# print the interesting parts of the results
print("Found", color.bold + str(res2['hits']['total']) + color.end, "results")
print()
for i, item in enumerate(interesting):
    print_res(item, i)
    print()

# ask user for opening a search result
# give the possibility to choose more than one result
while True:
    user_value = input("Type number to open, q to exit\n")
    try:
        want = int(user_value)
    except ValueError:
        if user_value == "q":
            sys.exit()
        else:
            print("Not a number")
            
    subprocess.call(["xdg-open", interesting[want]['path']])
            
