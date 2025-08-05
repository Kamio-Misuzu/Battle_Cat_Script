from bcDevice import device
from bcLogging import getLogger
import time
import random
import os
import traceback
import logging
from bcDetector import BattleCatDetector, ADBScreenshot

logger = getLogger('BCBattleCatDetector')


def main():
    if not device.available:
        logger.error("设备不可用，请检查连接")
        return

    device_id = device.name
    logger.info(f"使用设备ID: {device_id}")

    # 初始化ADB截图工具
    adb_screenshot = ADBScreenshot(device_id)

    # 检测目标模板
    img_paths = [
        r"F:\python\MC\BC\bcImg\YES.png",
        r"F:\python\MC\BC\bcImg\Battle_Start.png",
        r"F:\python\MC\BC\bcImg\OK.png",
        r"F:\python\MC\BC\bcImg\Battle_List.png"
    ]

    BL = ["Battle_List.png"]
    thresholds = [0.45, 0.45, 0.45, 0.45]
    # 猫咪出场栏坐标
    Battle_Po = [
        (760, 832), (970, 832), (1173, 832), (1403, 832), (1608, 832),
        (760, 986), (970, 986), (1173, 986), (1403, 986), (1608, 986)
    ]

    for img_path in img_paths:
        if not os.path.exists(img_path):
            logger.error(f"模板图片不存在: {img_path}")
            logger.error("请检查图片路径是否正确")
            return

    try:
        # 可以设置不同的阈值
        detector = BattleCatDetector(img_paths, thresholds=thresholds)
    except Exception as e:
        logger.error(f"检测器初始化失败: {e}")
        logger.error("程序无法启动，请检查错误")
        return

    # 检查设备连接
    if not device.check_device_connection(device_id):
        logger.error(f"设备 {device_id} 未连接")
        return

    logger.info(f"设备 {device_id} 连接正常")

    # 主循环
    loop_count = 0
    last_found_time = 0
    consecutive_fails = 0  # 连续失败计数器

    logger.info("进入主循环...")

    # 调试模式
    debug_mode = False

    while True:
        loop_count += 1
        logger.info(f"===== 循环开始 #{loop_count} =====")

        try:
            # 使用ADB截图
            cv_img = adb_screenshot.capture(save_debug=debug_mode)

            if cv_img is None:
                logger.warning("截图失败，等待后重试")
                time.sleep(1)
                consecutive_fails += 1
                if consecutive_fails > 5:
                    logger.error("连续截图失败超过5次，退出程序")
                    return
                continue

            # 重置连续失败计数器
            consecutive_fails = 0
            logger.info(f"截图成功，尺寸: {cv_img.shape[1]}x{cv_img.shape[0]}")

            # 查找目标按钮
            position, matched_template = detector.find_target(cv_img, debug=debug_mode)

            # 5次循环后关闭调试模式
            if loop_count >= 5:
                debug_mode = False

            if position:
                if matched_template in BL:
                    logger.info(f"检测到 {matched_template}，开始顺序点击所有位置")

                    # 从后向前遍历所有位置（索引从最后开始到0）
                    for i in range(len(Battle_Po) - 1, -1, -1):
                        click_pos = Battle_Po[i]
                        # 添加随机偏移
                        click_pos = detector.random_offset(click_pos, offset_range=1)

                        # 执行点击命令
                        cmd = f"adb -s {device_id} shell input tap {click_pos[0]} {click_pos[1]}"
                        logger.info(f"点击位置 {i + 1}/{len(Battle_Po)}: {click_pos}")
                        os.system(cmd)

                        # 等待0.1秒
                        time.sleep(0.1)

                    # 更新最后找到时间
                    last_found_time = time.time()
                    logger.info("所有位置点击完成")

                    # 等待一段时间后继续
                    wait_time = random.uniform(0.5, 1)
                    logger.info(f"等待 {wait_time:.1f} 秒...")
                    time.sleep(wait_time)
                    continue
                else:
                    current_time = time.time()
                    time_since_last = current_time - last_found_time

                    # 防止连续点击
                    if time_since_last < 2:
                        logger.info(f"找到按钮但距离上次点击仅 {time_since_last:.1f} 秒，跳过点击")
                        time.sleep(1)
                        continue

                    last_found_time = current_time
                    logger.info(f"找到 {matched_template} 按钮，位置: {position}")

                    # 添加随机偏移并点击
                    click_position = detector.random_offset(position, offset_range=4)
                    logger.info(f"点击位置: {click_position}")

            else:
                # 没有找到任何按钮，点击屏幕正中间
                center_x = cv_img.shape[1] // 2
                center_y = cv_img.shape[0] // 2
                click_position = (center_x, center_y)
                logger.info(f"未找到目标按钮，点击屏幕正中间: {click_position}")

                # 重置最后找到时间，避免连续点击限制
                last_found_time = 0

            # 使用ADB命令点击目标位置
            if 'click_position' in locals():
                cmd = f"adb -s {device_id} shell input tap {click_position[0]} {click_position[1]}"
                logger.info(f"执行点击命令: {cmd}")
                os.system(cmd)

            wait_time = random.uniform(0.5, 1)
            logger.info(f"等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)

            # 每5次循环检查一次设备连接
            if loop_count % 5 == 0:
                logger.info("检查设备连接状态...")
                if not device.check_device_connection(device_id):
                    logger.error("设备连接丢失！")
                    return
                logger.info("设备连接正常")

        except Exception as e:
            logger.error(f"主循环异常: {e}")
            logger.error(traceback.format_exc())
            time.sleep(3)


if __name__ == "__main__":
    try:
        logger.info("===== Battle Cat自动化战斗脚本 =====")
        logging.getLogger('bc').setLevel(logging.INFO)
        main()
    except Exception as e:
        logger.exception(f"程序异常: {e}")
    finally:
        logger.info("===== 程序结束 =====")
