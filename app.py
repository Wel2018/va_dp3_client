import threading
import numpy as np
import qt_material.themes
from toolbox.qt import qtbase
from toolbox.cam3d.cam3d_base import Camera3DBase
from .ui.ui_form import Ui_DemoWindow
from . import AppConfig, logger, APPCFG
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
        self.init(
            ui_logger=ui.txt_log,
            logger=logger,
            appcfg=AppConfig
        )
        self.post_init()
        self.set_theme("blue", 0)
        self.bind_clicked(ui.btn_run, self.play)
        self.add_log("程序初始化完成")

    def post_init(self):
        self.pressed_keys = set()
        self.appcfg = APPCFG
        self.camtype = APPCFG['camtype']
        
        # 摄像头
        zero_img = np.zeros((480, 640, 3), dtype=np.uint8)
        self.zero_img = qtbase.QPixmap(qtbase.cv2qt(zero_img))
        self.reset_viz()
        from toolbox.cam3d import load_cam3d
        camtypes_for_S_mode = APPCFG.get('camtypes_for_S_mode', [])
        self.cam: Camera3DBase = load_cam3d(
            self.camtype, 
            camtypes_for_S_mode, 
            is_start=1, 
            is_warmup=1)
        
        self.robot_cam_th = qtbase.CameraTask(
            qtbase.Camera3DWrapper(self.cam))
        self.robot_cam_th.bind(on_data=self.get_obs)
        self.add_th(self.TH_CAM, self.robot_cam_th, 1)
        
        # 点云可视化
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
