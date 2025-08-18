"""视觉模仿学习推理客户端"""

import os
from toolbox.qt import qtbase
from toolbox.core.logbase import get_logger
from toolbox.core.file_op import yaml_load


AppConfig = qtbase.QAppConfig(
    name = "VA 3D Diffusion Policy Realtime Inference Client",
    name_en = "VA 3D Diffusion Policy Realtime Inference Client",
    date="2025-08-18",
    version = "1.0.0",
    fontsize = 14
)
print(f"AppConfig={AppConfig}")


# 配置 -----------------------------------------------------------
APPSLOT = "va_dp3_client"
logger = get_logger(prefix="", name=APPSLOT)
cur_dir = os.path.dirname(os.path.abspath(__file__))
APPCFG: dict = yaml_load(f"{cur_dir}/appcfg.yaml")
print(f"APPCFG={APPCFG}")
THREAD_DEBUG = APPCFG['THREAD_DEBUG']
VERBOSE = APPCFG['VERBOSE']
BENCHMARK = APPCFG['BENCHMARK']
