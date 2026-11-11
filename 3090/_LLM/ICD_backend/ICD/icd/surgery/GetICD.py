from flask import Flask, request, jsonify, Response, stream_with_context
import requests
import json
import time
import os
import threading
import re
import tempfile
from elasticsearch import Elasticsearch

def get_icd(data, url):
    '''
    处理前端数据并送给各个agent，得到疾病ICD编码（待定）
    '''

