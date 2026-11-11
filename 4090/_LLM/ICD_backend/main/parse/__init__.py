import argparse

# 从run.sh中读取URL参数
parser = argparse.ArgumentParser(description='manual to this script')

parser.add_argument('--surgery_standardized_url', type=str, default='none')
parser.add_argument('--surgery_additional_url', type=str, default='none')
parser.add_argument('--surgery_another_coding_url', type=str, default='none')
parser.add_argument('--surgery_sorting_url', type=str, default='none')
parser.add_argument('--surgery_screening_url', type=str, default='none')
parser.add_argument('--no_surgery_standardized_url', type=str, default='none')
parser.add_argument('--no_surgery_screening_url', type=str, default='none')
parser.add_argument('--no_surgery_name_url', type=str, default='none')
parser.add_argument('--flask_url', type=str, default='http://localhost:6000/')
parser.add_argument('--output_dir', type=str, default='output')
parser.add_argument('--surgery_standardized_model', type=str, default='none')
parser.add_argument('--surgery_additional_model', type=str, default='none')
parser.add_argument('--surgery_another_coding_model', type=str, default='none')
parser.add_argument('--surgery_sorting_model', type=str, default='none')
parser.add_argument('--surgery_screening_model', type=str, default='none')
parser.add_argument('--no_surgery_standardized_model', type=str, default='none')
parser.add_argument('--no_surgery_screening_model', type=str, default='none')
parser.add_argument('--no_surgery_name_model', type=str, default='none')

# 解析命令行参数
args = parser.parse_args()
url = {    "surgery_standardized": args.surgery_standardized_url,
            "surgery_additional": args.surgery_additional_url,
            "surgery_another_coding": args.surgery_another_coding_url,
            "surgery_sorting": args.surgery_sorting_url,
            "surgery_screening": args.surgery_screening_url,
            "no_surgery_standardized": args.no_surgery_standardized_url,
            "no_surgery_screening": args.no_surgery_screening_url,
            "no_surgery_name": args.no_surgery_name_url
        }
model = {
    "surgery_standardized": args.surgery_standardized_model,
    "surgery_additional": args.surgery_additional_model,
    "surgery_another_coding": args.surgery_another_coding_model,
    "surgery_sorting": args.surgery_sorting_model,
    "surgery_screening": args.surgery_screening_model,
    "no_surgery_standardized": args.no_surgery_standardized_model,
    "no_surgery_screening": args.no_surgery_screening_model,
    "no_surgery_name": args.no_surgery_name_model
}

print("配置参数:")
print(f"URL配置: {url}")
print(f"模型配置: {model}")

flask_url = args.flask_url if args.flask_url[-1] == '/' else args.flask_url + '/'
output_dir = args.output_dir
port = flask_url.split(':')[-1].split('/')[0] if ':' in flask_url else '6000'

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