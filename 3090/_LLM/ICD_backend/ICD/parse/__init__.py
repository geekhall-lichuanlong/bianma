import argparse

# 从run.sh中读取URL参数
parser = argparse.ArgumentParser(description='manual to this script')
parser.add_argument('--disease_standardized_url', type=str, default='none')
parser.add_argument('--disease_potential_url', type=str, default='none')
parser.add_argument('--disease_potential_standardized_url', type=str, default='none')
parser.add_argument('--disease_main_diagnosis_url', type=str, default='none')
parser.add_argument('--disease_potential_verify_url', type=str, default='none')
parser.add_argument('--disease_screening_url', type=str, default='none')
parser.add_argument('--disease_bingli_url', type=str, default='none')
parser.add_argument('--disease_external_url', type=str, default='none')
parser.add_argument('--flask_url', type=str, default='http://localhost:5511/')
parser.add_argument('--output_dir', type=str, default='output')
parser.add_argument('--disease_standardized_model', type=str, default='none')
parser.add_argument('--disease_potential_model', type=str, default='none')
parser.add_argument('--disease_potential_standardized_model', type=str, default='none')
parser.add_argument('--disease_main_diagnosis_model', type=str, default='none')
parser.add_argument('--disease_potential_verify_model', type=str, default='none')
parser.add_argument('--disease_screening_model', type=str, default='none')
parser.add_argument('--disease_bingli_model', type=str, default='none')
parser.add_argument('--disease_external_model', type=str, default='none')


# 解析命令行参数
args = parser.parse_args()
url = {    "disease_standardized": args.disease_standardized_url,
            "disease_potential_extract": args.disease_potential_url,
            "disease_potential_standardized": args.disease_potential_standardized_url,
            "disease_main_diagnosis": args.disease_main_diagnosis_url,
            "disease_potential_verify": args.disease_potential_verify_url,
            "disease_screening": args.disease_screening_url,
            "disease_bingli": args.disease_bingli_url,
            "disease_external": args.disease_external_url
        }
model = {
    "disease_standardized": args.disease_standardized_model,
    "disease_potential_extract": args.disease_potential_model,
    "disease_potential_standardized": args.disease_potential_standardized_model,
    "disease_main_diagnosis": args.disease_main_diagnosis_model,
    "disease_potential_verify": args.disease_potential_verify_model,
    "disease_screening": args.disease_screening_model,
    "disease_bingli": args.disease_bingli_model,
    "disease_external": args.disease_external_model
}

print("配置参数:")
print(f"URL配置: {url}")
print(f"模型配置: {model}")

flask_url = args.flask_url if args.flask_url[-1] == '/' else args.flask_url + '/'
output_dir = args.output_dir
port = flask_url.split(':')[-1].split('/')[0] if ':' in flask_url else '5511'

# 获取调用模型的URL
def get_url(agent_name):
    '''
    获取各个智能体的URL
    '''
    return url.get(agent_name, "none")

# 获取Flask应用的URL
def get_flask_url():
    '''
    获取Flask应用的URL
    '''
    return flask_url


def get_output_dir():
    '''
    获取输出目录
    '''
    return output_dir

def get_port():
    '''
    获取Flask应用的端口
    '''
    return port

def get_model(agent_name):
    '''
    获取各个智能体的模型
    '''
    return model.get(agent_name, "none")
