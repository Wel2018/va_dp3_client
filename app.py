import threading
import numpy as np
from toolbox.qt import qtbase
from toolbox.qt import QTaskCamera
from toolbox.cam3d.cam3d_base import Camera3DWrapper
from toolbox.cam3d.cam3d_base import Camera3DBase
from .ui.ui_form import Ui_DemoWindow
from . import q_appcfg, logger
from .bgtask.pc_viz import RealTimePointCloudViewer


class MainWindow(qtbase.QApp):
    """应用具体实现"""
    # 定时器和线程名称
    TH_CAM = "cam"
    is_quit_confirm = 0  # 程序退出确认
    is_keyboard_ctrl = 1  # 键盘控制开关
    is_debug = 0

    def __init__(self, parent = None):
        ui = self.ui = Ui_DemoWindow()
        super().__init__(ui, parent, q_appcfg)
        self.pre_init()
        self.init(ui_logger=self.ui.txt_log, logger=logger)
        self.load_cam3d()
        self.post_init()
    
    def load_cam3d(self):
        # 摄像头
        zero_img = np.zeros((480, 640, 3), dtype=np.uint8)
        self.zero_img = qtbase.QPixmap(qtbase.cv2qt(zero_img))
        self.reset_viz()
        from toolbox.cam3d import load_cam3d
        # camtypes_for_S_mode = self.appcfg.get('camtypes_for_S_mode', [])
        self.cam: Camera3DBase = load_cam3d(
            self.APPCFG_DICT['camtype'], [], 
            is_start=1, 
            is_warmup=1)
        
        cam3d_wrapper = Camera3DWrapper(self.cam)
        self.robot_cam_th = QTaskCamera(cam3d_wrapper)
        self.robot_cam_th.bind(on_data=self.get_obs)
        self.add_th(self.TH_CAM, self.robot_cam_th, 1)
        
        # 点云可视化
        self.pc_viz_widget = RealTimePointCloudViewer(self.cam)
        self.replace_widget(self.ui.wd_bottom, self.pc_viz_widget)
        

    def post_init(self):
        self.set_theme("blue", 0)
        self.bind_clicked(self.ui.btn_run, self.play)
        self.bind_clicked(self.ui.btn_stop, self.stop_play)
        self.add_log("程序初始化完成", color="green")
        self.pc_viz_widget.update_point_cloud_bg()

    def stop_play(self):
        ...

    def play(self):
        """执行任务理解逻辑"""
        self.pc_viz_widget.update_point_cloud_bg()
        
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

    def keyPressEvent(self, event: qtbase.QKeyEvent):
        super().keyPressEvent(event)
        # print(self.pressed_keys)
        # 热重载 ctrl+r
        if self.is_keys_pressed([
            qtbase.qt_keys.Key_Control,
            qtbase.qt_keys.Key_R
        ]):
            self.hot_reload()
        
            
    def hot_reload(self):
        self.pre_init()
        self.init()
        self.post_init()
        self.add_log("hot reload")
        

def main():
    import sys
    qapp = qtbase.QApplication(sys.argv)
    # 设置全局默认字体
    qapp.setFont(qtbase.QFont("微软雅黑", 11))
    mapp = MainWindow()
    mapp.show()
    sys.exit(qapp.exec())
