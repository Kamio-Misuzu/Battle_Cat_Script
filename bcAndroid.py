import re, shutil, threading, cv2
import time
from airtest.core.android.adb import ADB
from airtest.core.android.android import Android as Airtest
from bcLogging import getLogger
import numpy
from bcConstants import *

logger = getLogger('BCAndroid')

if adb := shutil.which('adb'):
    logger.warning(f'Using Adb in PATH: {adb}')
    ADB.builtin_adb_path = staticmethod(lambda: adb)


class BCAndroid(Airtest):
    def __init__(self, serial=None, **kwargs):
        self.mutex = threading.Lock()
        self.package = None
        # 尝试连接设备
        try:
            if serial:
                super().__init__(serial, **kwargs)
                self.package = self._detect_battle_cats()
                self.name = self.serialno
                logger.info(f"已连接设备: {self.name}")
            else:
                logger.warning("未指定设备序列号")
                self.name = None
        except Exception as e:
            logger.exception(f"设备连接失败: {e}")
            self.name = None

    def _detect_battle_cats(self):
        """检测猫咪大战争是否正在运行"""
        # 获取当前顶层Activity
        top_activity = self.adb.shell('dumpsys activity top')

        # 检查猫咪大战争包名是否在输出中
        if BC_PACKAGE_NAME in top_activity:
            logger.info("猫咪大战争正在运行")
            return BC_PACKAGE_NAME

        # 检查进程列表
        processes = self.adb.shell('ps | grep ponos')
        if BC_PACKAGE_NAME in processes:
            logger.info("猫咪大战争在后台运行")
            return BC_PACKAGE_NAME

        logger.warning("猫咪大战争未运行")
        return None

    @property
    def available(self):
        """设备是否可用"""
        if not self.name:
            return False
        if self.touch_proxy.server_proc.poll() is None:
            return True
        self.name = None
        return False

    @staticmethod
    def enumDevices():
        """枚举可用设备"""
        return [i for i, _ in ADB().devices('device')]

    def is_battle_cats_running(self):
        """检查猫咪大战争是否运行"""
        return self.package == BC_PACKAGE_NAME


