"""视觉模仿学习推理客户端"""

from toolbox.qt import qtbase
from toolbox.core.logbase import get_logger


q_appcfg = qtbase.QAppConfig(
    name = "VA DP3 推理程序",
    name_en = "VA 3D Diffusion Policy Realtime Inference Client",
    date="2025-08-21",
    version = "1.0.0",
    fontsize = 14,
    slot="va_dp3_client",
    APPCFG_DICT=qtbase.get_appcfg(__file__),
)

print(f"QAppConfig={q_appcfg}")
logger = get_logger(q_appcfg.slot)


if q_appcfg.APPCFG_DICT['HOTRELOAD']:
    print("hotreload mode enabled")
    import jurigged
    jurigged.watch("projects")
