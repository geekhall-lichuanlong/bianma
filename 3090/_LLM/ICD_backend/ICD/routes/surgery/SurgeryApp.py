from flask import Blueprint, Flask, request, jsonify, Response, stream_with_context


surgery_app = Blueprint('surgery', __name__)    

def get_surgery_app():
    '''
    获取手术相关的Flask蓝图
    '''
    return surgery_app