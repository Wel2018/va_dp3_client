import threading
import numpy as np
from toolbox.qt import qtbase
from toolbox.cam3d.cam3d_base import Camera3DBase
from .ui.ui_form import Ui_DemoWindow
from . import AppConfig, logger, VERBOSE, THREAD_DEBUG, APPCFG, APPSLOT
from .bgtask.pc_viz import RealTimePointCloudViewer


class MainWindow(qtbase.IMainWindow):
    """应用具体实现"""
    # 定时器和线程名称
    TH_CAM = "cam"
    is_quit_confirm = 0  # 程序退出确认
    is_keyboard_ctrl = 1  # 键盘控制开关
    is_debug = 0

    def __init__(self, parent = None):
        ui = self.ui = Ui_DemoWindow()
        super().__init__(ui, parent)

        # 初始化
        self.init(
            confcache_name=APPSLOT,
            apptitle=AppConfig.title,
            ui_logger=ui.txt_log,
            logger=logger,
            fontsize=AppConfig.fontsize,
        )

        # 绑定点击事件
        self.bind_clicked(ui.btn_run, self.play)

        # 摄像头
        zero_img = np.zeros((480, 640, 3), dtype=np.uint8)
        self.zero_img = qtbase.QPixmap(qtbase.cv2qt(zero_img))
        self.reset_viz()

        #self.tcost = Timecost(0, 1)
        self.pressed_keys = set()
        self.appcfg = APPCFG
        self.camtype = APPCFG['camtype']
        
        from toolbox.cam3d import load_cam3d
        camtypes_for_S_mode = APPCFG.get('camtypes_for_S_mode', [])
        self.cam: Camera3DBase = load_cam3d(
            self.camtype, camtypes_for_S_mode, is_start=1, is_warmup=1)
        self.robot_cam_th = qtbase.CameraTask(
            qtbase.Camera3DWrapper(self.cam))
        self.robot_cam_th.bind(on_data=self.get_obs)
        self.add_th(self.TH_CAM, self.robot_cam_th, 1)
        self.add_log("程序初始化完成")
        # 检查服务器是否能够正常连接
        # self.add_timer(self.TIMER_ROBOT_STATE, 100, self.refresh_state, 1)
        self.cam_read_conf = {
            "is_sync": 1,
            "is_bgr": 1,
            "read_color": 1,
            "read_depth": 1,
            "read_pc": 1
        }
        
        self.pc_viz_widget = RealTimePointCloudViewer(self.cam)
        self.replace_widget(self.ui.wd_bottom, self.pc_viz_widget)


    def play(self):
        """执行任务理解逻辑"""
        self.pc_viz_widget.update_point_cloud()
        
    def reset_viz(self):
        self.pix_left = self.zero_img
        self.pix_right = self.zero_img

    def paintEvent(self, event: qtbase.QtGui.QPaintEvent) -> None:
        """图像显示区支持自适应缩放"""
        ui = self.ui
        self._resize_and_scaled(ui.lb_left, ui.wd_left, self.pix_left)
        self._resize_and_scaled(ui.lb_right, ui.wd_right, self.pix_right)
        return super().paintEvent(event)

    def close_ready(self):
        ...


    def get_obs(self, frames: dict):
        # if not frames['ret']: return
        self.pix_left = qtbase.QPixmap(qtbase.cv2qt(frames['v1']))
        self.pix_right = qtbase.QPixmap(qtbase.cv2qt(frames['v2']))


def main():
    import sys
    qapp = qtbase.QApplication(sys.argv)
    # 设置全局默认字体
    qapp.setFont(qtbase.QFont("微软雅黑", 11))
    mapp = MainWindow()
    mapp.show()
    sys.exit(qapp.exec())
