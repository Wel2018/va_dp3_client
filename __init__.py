"""视觉模仿学习推理客户端"""

from toolbox.qt import qtbase
from toolbox.core.logbase import get_logger
APPCFG = qtbase.get_appcfg(__file__)


AppConfig = qtbase.QAppConfig(
    name = "VA DP3 推理程序",
    name_en = "VA 3D Diffusion Policy Realtime Inference Client",
    date="2025-08-18",
    version = "1.0.0",
    fontsize = 14,
    slot="va_dp3_client",
    appcfg=APPCFG,
)

print(f"AppConfig={AppConfig}")
logger = get_logger(AppConfig.slot)
