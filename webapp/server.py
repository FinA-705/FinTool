"""
FastAPI服务器主入口
"""

import sys
from pathlib import Path

# 添加项目根目录到sys.path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from webapp.app import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
