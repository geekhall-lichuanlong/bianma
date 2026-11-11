from routes.app import app
from parse import get_port

if __name__ == "__main__":
    # 启动Flask应用
    app.run(host="0.0.0.0", port=get_port())

