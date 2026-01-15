"""视觉模仿学习推理客户端"""

from toolbox.qt import qtbase
from .version import __version__
from .version import __update_timestamp__


q_appcfg = qtbase.QAppConfig(
    name = "VA DP3 推理程序",
    name_en = "VA 3D Diffusion Policy Realtime Inference Client",
    date=__update_timestamp__,
    version = __version__,
    fontsize = 14,
    slot="va_dp3_client",
    APPCFG_DICT=qtbase.get_appcfg(__file__),
)
