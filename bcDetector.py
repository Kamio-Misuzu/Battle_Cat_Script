from bcLogging import getLogger
import cv2
import time
import random
import os
import subprocess
import threading

logger = getLogger('BCBattleCatDetector')

class BattleCatDetector:

    def __init__(self, img_paths, thresholds=None):
        self.templates = []

        if thresholds is None:
            thresholds = [0.4] * len(img_paths)

        for i, img_path in enumerate(img_paths):
            if not os.path.exists(img_path):
                logger.error(f"目标图片不存在: {img_path}")
                raise FileNotFoundError(f"目标图片不存在: {img_path}")

            target_img = cv2.imread(img_path)
            if target_img is None:
                logger.error(f"无法加载目标图片: {img_path}")
                raise ValueError(f"无法加载目标图片: {img_path}")

            img_height, img_width = target_img.shape[:2]
            logger.info(
                f"加载目标图片 {os.path.basename(img_path)} 成功，尺寸: {img_width}x{img_height}，阈值: {thresholds[i]}")

            self.templates.append({
                "image": target_img,
                "width": img_width,
                "height": img_height,
                "threshold": thresholds[i],
                "name": os.path.basename(img_path)
            })

    def find_target(self, screen_img, debug=False):
        try:
            # 尝试匹配所有模板
            for template in self.templates:
                target_img = template["image"]
                threshold = template["threshold"]
                img_width = template["width"]
                img_height = template["height"]
                template_name = template["name"]

                # scales可以用来调整屏幕尺寸大小的问题
                scales = [0.8, 0.9, 1.0, 1.1, 1.2]
                max_val = 0
                max_loc = None
                best_scale = 1.0
                best_size = (img_width, img_height)

                for scale in scales:
                    # 调整模板大小
                    resized_template = cv2.resize(
                        target_img,
                        (int(img_width * scale),
                         int(img_height * scale)))
                    resized_height, resized_width = resized_template.shape[:2]

                    # 如果调整后的模板比屏幕大，跳过
                    if resized_height > screen_img.shape[0] or resized_width > screen_img.shape[1]:
                        continue

                    # 主要的算法地方: 模板匹配
                    result = cv2.matchTemplate(screen_img, resized_template, cv2.TM_CCOEFF_NORMED)
                    _, local_max_val, _, local_max_loc = cv2.minMaxLoc(result)

                    # 更新最佳匹配
                    if local_max_val > max_val:
                        max_val = local_max_val
                        max_loc = local_max_loc
                        best_scale = scale
                        best_size = (resized_width, resized_height)

                logger.info(f"模板 {template_name} 最佳匹配值: {max_val:.4f} (阈值: {threshold}), 尺度: {best_scale}")

                # 保存调试图片到本地
                if debug and max_loc:
                    debug_img = screen_img.copy()
                    top_left = max_loc
                    bottom_right = (top_left[0] + best_size[0], top_left[1] + best_size[1])
                    cv2.rectangle(debug_img, top_left, bottom_right, (0, 0, 255), 3)

                    text = f"{template_name}: {max_val:.4f} Scale: {best_scale}"
                    cv2.putText(debug_img, text, (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    debug_path = f"debug_match_{template_name}_{time.strftime('%H%M%S')}.png"
                    cv2.imwrite(debug_path, debug_img)
                    logger.info(f"匹配调试图已保存: {debug_path}")

                # 检查匹配度是否超过阈值
                if max_val >= threshold and max_loc:
                    center_x = max_loc[0] + best_size[0] // 2
                    center_y = max_loc[1] + best_size[1] // 2
                    return (center_x, center_y), template_name

            # 没有匹配到任何模板
            return None, None

        except Exception as e:
            logger.error(f"图片匹配失败: {e}")
            return None, None

    @staticmethod
    def random_offset(position, offset_range=5):
        """添加随机偏移"""
        x, y = position
        x += random.randint(-offset_range, offset_range)
        y += random.randint(-offset_range, offset_range)
        return (x, y)


class ADBScreenshot:
    """截图方法：保存到设备再拉取"""

    def __init__(self, device_id):
        self.device_id = device_id
        self.device_path = "/sdcard/screen_temp.png"
        self.local_path = "screen_temp.png"
        self.lock = threading.Lock()

    def capture(self, save_debug=False):
        """捕获屏幕截图"""
        with self.lock:
            try:
                # 使用标准截图命令
                cmd_screencap = f"adb -s {self.device_id} shell screencap -p {self.device_path}"
                screencap_result = subprocess.run(cmd_screencap, shell=True,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE,
                                                  timeout=10)

                if screencap_result.returncode != 0:
                    logger.error(f"设备截图失败: {screencap_result.stderr.decode('utf-8', errors='ignore')}")
                    return None

                # 添加延迟确保文件保存
                time.sleep(0.2)

                # 从设备拉取截图
                cmd_pull = f"adb -s {self.device_id} pull {self.device_path} {self.local_path}"
                pull_result = subprocess.run(cmd_pull, shell=True,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             timeout=10)

                if pull_result.returncode != 0:
                    logger.error(f"拉取截图失败: {pull_result.stderr.decode('utf-8', errors='ignore')}")
                    return None

                # 添加延迟确保文件传输
                time.sleep(0.1)

                # 读取本地截图文件
                if not os.path.exists(self.local_path):
                    logger.error(f"本地截图文件不存在: {self.local_path}")
                    return None

                img = cv2.imread(self.local_path)

                # 保存调试截图
                if save_debug and img is not None:
                    debug_path = f"debug_screen_{time.strftime('%H%M%S')}.png"
                    cv2.imwrite(debug_path, img)
                    logger.info(f"调试截图已保存: {debug_path}")

                return img
            except subprocess.TimeoutExpired:
                logger.error("截图命令超时")
                return None
            except Exception as e:
                logger.error(f"截图异常: {e}")
                return None
            finally:
                # 清理临时文件
                try:
                    if os.path.exists(self.local_path):
                        os.remove(self.local_path)
                    adb_clean = f"adb -s {self.device_id} shell rm {self.device_path}"
                    subprocess.run(adb_clean, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   timeout=5)
                except Exception as clean_error:
                    logger.warning(f"清理临时文件失败: {clean_error}")