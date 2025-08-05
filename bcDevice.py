from bcAndroid import BCAndroid
from bcLogging import getLogger
import subprocess

logger = getLogger('BCDevice')


class BCDevice:
    def __init__(self, name=None):
        if name is None:
            devices = BCAndroid.enumDevices()
            if devices:
                name = devices[0]
                logger.info(f"自动选择设备: {name}")
            else:
                logger.error("未找到可用设备")

        self.android = BCAndroid(name)
        self.name = self.android.name
        print("当前设备名:", self.android.name)

    @property
    def available(self):
        return self.android.available

    def is_battle_cats_running(self):
        return self.android.is_battle_cats_running()

    def check_device_connection(self, device_id):
        """检查设备是否连接"""
        try:
            result = subprocess.run(f"adb -s {device_id} shell getprop ro.serialno", shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.warning("设备状态检查超时")
            return False
        except Exception as e:
            logger.error(f"设备状态检查异常: {e}")
            return False


# 全局设备实例
device = BCDevice()
