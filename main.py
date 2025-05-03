#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import subprocess
import platform
import shutil
import re
import glob
import time
import threading
from pathlib import Path
from colorama import init, Fore, Style

# 初始化colorama
init()

# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 进度条相关变量
progress_thread = None
stop_progress = False


def print_progress_bar(prefix="", suffix="", length=50):
    """打印进度条动画"""
    global stop_progress
    stop_progress = False

    # 进度条字符
    animation = [
        "[■□□□□□□□□□]",
        "[■■□□□□□□□□]",
        "[■■■□□□□□□□]",
        "[■■■■□□□□□□]",
        "[■■■■■□□□□□]",
        "[■■■■■■□□□□]",
        "[■■■■■■■□□□]",
        "[■■■■■■■■□□]",
        "[■■■■■■■■■□]",
        "[■■■■■■■■■■]"
    ]

    i = 0
    while not stop_progress:
        sys.stdout.write(
            f"\r{prefix} {animation[i % len(animation)]} {suffix}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1

    # 清空进度条行
    sys.stdout.write("\r" + " " * (len(prefix) +
                     len(suffix) + length + 5) + "\r")
    sys.stdout.flush()


def start_progress(prefix="处理中", suffix="请稍候..."):
    """启动进度条线程"""
    global progress_thread
    progress_thread = threading.Thread(
        target=print_progress_bar, args=(prefix, suffix))
    progress_thread.daemon = True
    progress_thread.start()


def stop_progress_bar(success=True, success_msg="完成!", error_msg="失败!"):
    """停止进度条显示"""
    global stop_progress
    stop_progress = True

    if progress_thread:
        progress_thread.join(timeout=0.5)

    if success:
        print(f"{Fore.GREEN}✓ {success_msg}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ {error_msg}{Style.RESET_ALL}")

def print_header():
    """打印程序头部信息"""
    print(f"{Fore.CYAN}========================={Style.RESET_ALL}")
    print(f"{Fore.CYAN}  ESP32 唤醒词管理工具  {Style.RESET_ALL}")
    print(f"{Fore.CYAN}========================={Style.RESET_ALL}")
    print()

def check_prerequisites():
    """检查必要的工具和目录是否存在"""
    print(f"{Fore.YELLOW}检查必要组件...{Style.RESET_ALL}")

    # 检查esptool
    try:
        subprocess.run(["esptool.py", "--version"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        print(f"{Fore.GREEN}✓ esptool.py 已安装{Style.RESET_ALL}")
    except (FileNotFoundError, subprocess.SubprocessError):
        try:
            subprocess.run(["esptool", "--version"], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, check=False)
            print(f"{Fore.GREEN}✓ esptool 已安装{Style.RESET_ALL}")
        except (FileNotFoundError, subprocess.SubprocessError):
            print(f"{Fore.RED}✗ esptool 未安装，请先安装 esptool{Style.RESET_ALL}")
            print(f"  安装命令: pip install esptool")
            return False

    # 检查esp-sr目录
    esp_sr_path = os.path.join(CURRENT_DIR, "esp-sr")
    if not os.path.exists(esp_sr_path):
        print(f"{Fore.RED}✗ esp-sr 目录不存在{Style.RESET_ALL}")
        return False
    else:
        print(f"{Fore.GREEN}✓ esp-sr 目录已找到{Style.RESET_ALL}")

    # 检查build目录，不存在则创建
    build_path = os.path.join(CURRENT_DIR, "build")
    if not os.path.exists(build_path):
        os.makedirs(os.path.join(build_path, "srmodels"), exist_ok=True)
        print(f"{Fore.YELLOW}✓ build 目录已创建{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}✓ build 目录已找到{Style.RESET_ALL}")

    print()
    return True


def select_wake_word_category():
    """选择唤醒词类别"""
    categories = {
        "1": {"name": "WakeNet9", "prefix": "CONFIG_SR_WN_WN9_"},
        "2": {"name": "WakeNet9s", "prefix": "CONFIG_SR_WN_WN9S_"}
    }

    print(f"{Fore.YELLOW}请选择唤醒词类别:{Style.RESET_ALL}")
    for key, value in categories.items():
        print(f"{Fore.GREEN}{key}. {value['name']}{Style.RESET_ALL}")

    while True:
        choice = input(
            f"{Fore.YELLOW}请选择 [1-{len(categories)}]: {Style.RESET_ALL}")
        if choice in categories:
            return categories[choice]
        print(f"{Fore.RED}无效选择，请重试{Style.RESET_ALL}")


def select_multinet_model():
    """选择语音识别模型"""
    multinet_models = {
        "1": {"name": "不使用语音识别模型", "config": "CONFIG_SR_MN_CN_NONE=y"},
        "2": {"name": "中文语音识别 MultiNet6 (量化版)", "config": "CONFIG_SR_MN_CN_MULTINET6_QUANT=y"}
    }

    print(f"{Fore.YELLOW}请选择语音识别模型:{Style.RESET_ALL}")
    for key, value in multinet_models.items():
        print(f"{Fore.GREEN}{key}. {value['name']}{Style.RESET_ALL}")

    while True:
        choice = input(
            f"{Fore.YELLOW}请选择 [1-{len(multinet_models)}] (默认2): {Style.RESET_ALL}") or "2"
        if choice in multinet_models:
            return multinet_models[choice]
        print(f"{Fore.RED}无效选择，请重试{Style.RESET_ALL}")


def select_wake_word(category_prefix):
    """选择唤醒词"""
    wake_words = {
        # 中文唤醒词
        "1": {"name": "你好小智", "id": "NIHAOXIAOZHI_TTS"},
        "2": {"name": "你好小鑫", "id": "NIHAOXIAOXIN_TTS"},
        "3": {"name": "小爱同学", "id": "XIAOAITONGXUE"},
        "4": {"name": "小美同学", "id": "XIAOMEITONGXUE_TTS"},
        "5": {"name": "喵喵同学", "id": "MIAOMIAOTONGXUE_TTS"},
        "6": {"name": "小龙小龙", "id": "XIAOLONGXIAOLONG_TTS"},
        # 英文唤醒词
        "7": {"name": "Hi ESP", "id": "HIESP"},
        "8": {"name": "Hi 乐鑫", "id": "HILEXIN"},
        "9": {"name": "Hi Jason", "id": "HIJASON_TTS2"},
        "10": {"name": "Hi M Five", "id": "HIMFIVE"},
        "11": {"name": "Hi 瓦力", "id": "HIWALLE_TTS2"},
        "12": {"name": "Hi 小星", "id": "HIXIAOXING_TTS"},
        "13": {"name": "Hi 喵喵", "id": "HIMIAOMIAO_TTS"},
        "14": {"name": "Hi 莉莉", "id": "HILILI_TTS"},
        "15": {"name": "Hi 泰力", "id": "HITELLY_TTS"},
        "16": {"name": "Hi 小巫", "id": "HAIXIAOWU_TTS"},
        # 其他流行唤醒词
        "17": {"name": "Alexa", "id": "ALEXA"},
        "18": {"name": "Jarvis", "id": "JARVIS_TTS"},
        "19": {"name": "Computer", "id": "COMPUTER_TTS"},
        "20": {"name": "Hey Willow", "id": "HEYWILLOW_TTS"}
    }

    print(f"{Fore.YELLOW}请选择唤醒词:{Style.RESET_ALL}")
    # 按类别分组显示
    print(f"{Fore.CYAN}中文唤醒词:{Style.RESET_ALL}")
    for i in range(1, 7):
        print(
            f"{Fore.GREEN}{i}. {wake_words[str(i)]['name']}{Style.RESET_ALL}")

    print(f"{Fore.CYAN}Hi 系列唤醒词:{Style.RESET_ALL}")
    for i in range(7, 17):
        print(
            f"{Fore.GREEN}{i}. {wake_words[str(i)]['name']}{Style.RESET_ALL}")

    print(f"{Fore.CYAN}其他唤醒词:{Style.RESET_ALL}")
    for i in range(17, 21):
        print(
            f"{Fore.GREEN}{i}. {wake_words[str(i)]['name']}{Style.RESET_ALL}")

    while True:
        choice = input(
            f"{Fore.YELLOW}请选择 [1-{len(wake_words)}]: {Style.RESET_ALL}")
        if choice in wake_words:
            wake_word = wake_words[choice]
            wake_word["config"] = f"{category_prefix}{wake_word['id']}=y"
            return wake_word
        print(f"{Fore.RED}无效选择，请重试{Style.RESET_ALL}")


def scan_partition_tables():
    """扫描项目中的分区表"""
    print(f"{Fore.YELLOW}正在扫描分区表文件...{Style.RESET_ALL}")

    # 搜索分区表文件
    partition_files = []

    # 从当前目录及上级目录查找所有CSV文件
    search_dirs = [
        CURRENT_DIR,
        os.path.join(CURRENT_DIR, ".."),
        os.path.join(CURRENT_DIR, "..", ".."),
    ]

    for search_dir in search_dirs:
        for file in glob.glob(os.path.join(search_dir, "*.csv")):
            # 检查是否是分区表文件（包含model,data,spiffs等典型内容）
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if any(keyword in content for keyword in ["app,", "data,", "spiffs", "model"]):
                        partition_files.append(file)
            except:
                continue

    # 如果存在platformio.ini，尝试解析它以找到分区表路径
    platformio_ini = os.path.join(CURRENT_DIR, "..", "platformio.ini")
    if os.path.exists(platformio_ini):
        try:
            with open(platformio_ini, "r", encoding="utf-8") as f:
                content = f.read()
                # 查找board_build.partitions设置
                partition_match = re.search(
                    r'board_build.(?:arduino.)?partitions\s*=\s*(.+)', content)
                if partition_match:
                    partition_path = partition_match.group(1).strip()
                    # 移除引号（如果有）
                    partition_path = partition_path.strip('"\'')
                    # 转换为绝对路径
                    if not os.path.isabs(partition_path):
                        partition_path = os.path.join(
                            os.path.dirname(platformio_ini), partition_path)
                    if os.path.exists(partition_path) and partition_path not in partition_files:
                        partition_files.insert(
                            0, partition_path)  # 将找到的路径添加到列表最前面
        except Exception as e:
            print(f"{Fore.YELLOW}无法解析platformio.ini: {str(e)}{Style.RESET_ALL}")

    if not partition_files:
        print(f"{Fore.RED}未找到任何分区表文件!{Style.RESET_ALL}")
        return None

    # 显示找到的分区表
    print(f"{Fore.GREEN}找到 {len(partition_files)} 个分区表文件:{Style.RESET_ALL}")
    for i, file in enumerate(partition_files, 1):
        print(f"{Fore.GREEN}{i}. {os.path.basename(file)} ({file}){Style.RESET_ALL}")

    # 用户选择
    while True:
        try:
            choice = int(
                input(f"{Fore.YELLOW}请选择分区表文件 [1-{len(partition_files)}]: {Style.RESET_ALL}"))
            if 1 <= choice <= len(partition_files):
                return partition_files[choice-1]
            print(f"{Fore.RED}无效选择，请重试{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}请输入数字{Style.RESET_ALL}")


def get_partition_info(partition_file):
    """从分区表中获取model和voice_data分区的信息"""
    print(f"{Fore.YELLOW}正在分析分区表: {os.path.basename(partition_file)}{Style.RESET_ALL}")

    partition_info = {
        "model": {"address": "0x710000", "size": "0x5E0000"},  # 默认值
        "voice_data": {"address": "0xCF0000", "size": "0x300000"}  # 默认值
    }

    try:
        with open(partition_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = [part.strip() for part in line.split(",")]
                if len(parts) >= 5:
                    name = parts[0].lower()
                    if name == "model":
                        partition_info["model"]["address"] = parts[3]
                        partition_info["model"]["size"] = parts[4]
                        print(
                            f"{Fore.GREEN}找到model分区: 地址={parts[3]}, 大小={parts[4]}{Style.RESET_ALL}")
                    elif name == "voice_data":
                        partition_info["voice_data"]["address"] = parts[3]
                        partition_info["voice_data"]["size"] = parts[4]
                        print(
                            f"{Fore.GREEN}找到voice_data分区: 地址={parts[3]}, 大小={parts[4]}{Style.RESET_ALL}")

        # 转换大小为人类可读的格式
        for partition in partition_info:
            size_hex = partition_info[partition]["size"]
            if size_hex.startswith("0x"):
                size_bytes = int(size_hex, 16)
                size_mb = size_bytes / (1024 * 1024)
                partition_info[partition]["size_readable"] = f"{size_mb:.2f} MB"
            else:
                partition_info[partition]["size_readable"] = size_hex

        print(
            f"{Fore.GREEN}model分区大小: {partition_info['model']['size_readable']}{Style.RESET_ALL}")
        print(
            f"{Fore.GREEN}voice_data分区大小: {partition_info['voice_data']['size_readable']}{Style.RESET_ALL}")

        return partition_info
    except Exception as e:
        print(f"{Fore.RED}解析分区表出错: {str(e)}{Style.RESET_ALL}")
        return partition_info


def generate_sdkconfig(category, wake_word, multinet_model):
    """生成sdkconfig文件"""
    print(f"{Fore.YELLOW}正在生成sdkconfig文件...{Style.RESET_ALL}")

    sdkconfig_content = f"""#
# ESP Speech Recognition
#
CONFIG_MODEL_IN_FLASH=y
CONFIG_USE_AFE=y
CONFIG_AFE_INTERFACE_V1=y
CONFIG_USE_WAKENET=y
CONFIG_USE_MULTINET=y
{multinet_model['config']}
# {wake_word['name']}
{wake_word['config']}
"""

    # 生成文件名
    sdkconfig_filename = f"{wake_word['id'].lower()}.sdkconfig"
    sdkconfig_path = os.path.join(CURRENT_DIR, sdkconfig_filename)

    # 写入文件
    try:
        with open(sdkconfig_path, "w", encoding="utf-8") as f:
            f.write(sdkconfig_content)
        print(f"{Fore.GREEN}配置文件已生成: {sdkconfig_filename}{Style.RESET_ALL}")
        return sdkconfig_path
    except Exception as e:
        print(f"{Fore.RED}生成配置文件失败: {str(e)}{Style.RESET_ALL}")
        return None

def select_com_port():
    """选择COM端口"""
    if platform.system() == "Windows":
        from serial.tools import list_ports
        ports = list(list_ports.comports())
        if not ports:
            print(f"{Fore.RED}未找到可用的COM端口{Style.RESET_ALL}")
            return input(f"{Fore.YELLOW}请手动输入COM端口 (例如 COM3): {Style.RESET_ALL}")

        print(f"{Fore.YELLOW}可用的COM端口:{Style.RESET_ALL}")
        for i, port in enumerate(ports, 1):
            print(
                f"{Fore.GREEN}{i}. {port.device} - {port.description}{Style.RESET_ALL}")

        while True:
            try:
                choice = int(
                    input(f"{Fore.YELLOW}请选择COM端口 [1-{len(ports)}]: {Style.RESET_ALL}"))
                if 1 <= choice <= len(ports):
                    return ports[choice-1].device
                print(f"{Fore.RED}无效选择，请重试{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}请输入数字{Style.RESET_ALL}")
    else:
        # 在Linux/Mac上列出/dev下的tty设备
        if platform.system() == "Linux":
            base_path = "/dev/"
            search_pattern = "ttyUSB*"
        else:  # macOS
            base_path = "/dev/"
            search_pattern = "tty.usbserial*"

        ports = list(Path(base_path).glob(search_pattern))
        if not ports:
            return input(f"{Fore.YELLOW}请手动输入串口设备 (例如 /dev/ttyUSB0): {Style.RESET_ALL}")

        print(f"{Fore.YELLOW}可用的串口设备:{Style.RESET_ALL}")
        for i, port in enumerate(ports, 1):
            print(f"{Fore.GREEN}{i}. {port}{Style.RESET_ALL}")

        while True:
            try:
                choice = int(
                    input(f"{Fore.YELLOW}请选择串口设备 [1-{len(ports)}]: {Style.RESET_ALL}"))
                if 1 <= choice <= len(ports):
                    return str(ports[choice-1])
                print(f"{Fore.RED}无效选择，请重试{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}请输入数字{Style.RESET_ALL}")


def generate_model(sdkconfig_path):
    """生成唤醒词模型"""
    print(f"{Fore.YELLOW}正在生成唤醒词模型...{Style.RESET_ALL}")

    # 确保build/srmodels目录存在
    build_path = os.path.join(CURRENT_DIR, "build")
    os.makedirs(os.path.join(build_path, "srmodels"), exist_ok=True)

    # ESP-SR目录
    esp_sr_path = os.path.join(CURRENT_DIR, "esp-sr")

    # 运行movemodel.py脚本
    movemodel_path = os.path.join(esp_sr_path, "model", "movemodel.py")
    cmd = [
        sys.executable,  # 当前Python解释器
        movemodel_path,
        "-d1", sdkconfig_path,
        "-d2", esp_sr_path,
        "-d3", build_path
    ]

    try:
        # 启动进度条
        start_progress(prefix=f"{Fore.YELLOW}生成模型中",
                       suffix="请稍候...{Style.RESET_ALL}")

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True)

        if "Recommended model partition size" in result.stdout:
            # 停止进度条
            stop_progress_bar(success=True, success_msg="模型生成成功")
            return True
        else:
            # 停止进度条
            stop_progress_bar(success=False, error_msg="模型生成过程中出现问题")
            print(result.stderr)
            return False
    except subprocess.CalledProcessError as e:
        # 停止进度条
        stop_progress_bar(success=False, error_msg=f"模型生成失败: {e}")
        print(e.stderr)
        return False


def flash_model(port, model_address):
    """烧写模型到ESP32"""
    print(f"{Fore.YELLOW}正在准备烧写模型到设备 {port}...{Style.RESET_ALL}")

    srmodels_bin = os.path.join(
        CURRENT_DIR, "build", "srmodels", "srmodels.bin")

    if not os.path.exists(srmodels_bin):
        print(f"{Fore.RED}✗ 模型文件不存在: {srmodels_bin}{Style.RESET_ALL}")
        return False

    # 使用2000000波特率烧写模型
    baud_rate = "2000000"

    # 使用esptool烧写模型
    tool_name = "esptool.py" if shutil.which("esptool.py") else "esptool"
    cmd = [
        tool_name,
        "--port", port,
        "--baud", baud_rate,
        "--before", "default_reset",
        "--after", "hard_reset",
        "write_flash",
        model_address, srmodels_bin
    ]

    try:
        print(f"{Fore.CYAN}执行烧写命令: {' '.join(cmd)}{Style.RESET_ALL}")

        # 启动进度条
        start_progress(prefix=f"{Fore.YELLOW}烧写模型中",
                       suffix=f"地址: {model_address}{Style.RESET_ALL}")

        # 执行烧写命令
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True)

        # 停止进度条
        stop_progress_bar(
            success=True, success_msg=f"模型烧写成功到地址 {model_address}")
        return True
    except subprocess.CalledProcessError as e:
        stop_progress_bar(success=False, error_msg=f"模型烧写失败: {e}")
        print(e.stderr)
        return False


def flash_tts_voice_data(port, voice_data_address):
    """烧写TTS语音数据到ESP32"""
    print(f"{Fore.YELLOW}是否需要烧写TTS语音数据? [y/N]: {Style.RESET_ALL}", end="")
    choice = input().strip().lower()

    if choice != 'y':
        return True

    print(f"{Fore.YELLOW}正在准备烧写TTS语音数据到设备 {port}...{Style.RESET_ALL}")

    tts_data_path = os.path.join(
        CURRENT_DIR, "esp-sr", "esp-tts", "esp_tts_chinese",
        "esp_tts_voice_data_xiaoxin_small.dat"
    )

    if not os.path.exists(tts_data_path):
        print(f"{Fore.RED}✗ TTS数据文件不存在: {tts_data_path}{Style.RESET_ALL}")
        return False

    # 使用2000000波特率烧写TTS数据
    baud_rate = "2000000"

    # 使用esptool烧写TTS数据
    tool_name = "esptool.py" if shutil.which("esptool.py") else "esptool"
    cmd = [
        tool_name,
        "--port", port,
        "--baud", baud_rate,
        "--before", "default_reset",
        "--after", "hard_reset",
        "write_flash",
        voice_data_address, tts_data_path
    ]

    try:
        print(f"{Fore.CYAN}执行烧写命令: {' '.join(cmd)}{Style.RESET_ALL}")

        # 启动进度条
        start_progress(prefix=f"{Fore.YELLOW}烧写TTS数据中",
                       suffix=f"地址: {voice_data_address}{Style.RESET_ALL}")

        # 执行烧写命令
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True)

        # 停止进度条
        stop_progress_bar(success=True, success_msg="TTS数据烧写成功")
        return True
    except subprocess.CalledProcessError as e:
        stop_progress_bar(success=False, error_msg=f"TTS数据烧写失败: {e}")
        print(e.stderr)
        return False

def main():
    """主函数"""
    print_header()

    if not check_prerequisites():
        sys.exit(1)

    # 步骤1：选择唤醒词类别
    category = select_wake_word_category()
    print(f"{Fore.CYAN}已选择唤醒词类别: {category['name']}{Style.RESET_ALL}")

    # 步骤2：选择唤醒词
    wake_word = select_wake_word(category['prefix'])
    print(f"{Fore.CYAN}已选择唤醒词: {wake_word['name']}{Style.RESET_ALL}")

    # 步骤3：选择语音识别模型（可选）
    multinet_model = select_multinet_model()
    print(f"{Fore.CYAN}已选择语音识别模型: {multinet_model['name']}{Style.RESET_ALL}")

    # 步骤4：生成sdkconfig文件
    sdkconfig_path = generate_sdkconfig(category, wake_word, multinet_model)
    if not sdkconfig_path:
        sys.exit(1)

    # 步骤5：扫描并选择分区表文件
    partition_file = scan_partition_tables()
    if not partition_file:
        # 使用默认分区地址
        partition_info = {
            "model": {"address": "0x710000", "size": "0x5E0000", "size_readable": "5.88 MB"},
            "voice_data": {"address": "0xCF0000", "size": "0x300000", "size_readable": "3.00 MB"}
        }
        print(f"{Fore.YELLOW}使用默认分区信息{Style.RESET_ALL}")
    else:
        # 分析分区表获取地址和大小信息
        partition_info = get_partition_info(partition_file)

    # 步骤6：生成模型
    if not generate_model(sdkconfig_path):
        sys.exit(1)

    # 步骤7：选择COM端口
    port = select_com_port()

    # 步骤8：烧写模型
    if not flash_model(port, partition_info["model"]["address"]):
        sys.exit(1)

    # 步骤9：烧写TTS语音数据
    flash_tts_voice_data(port, partition_info["voice_data"]["address"])

    print(f"\n{Fore.GREEN}所有操作已完成!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}已成功配置唤醒词: {wake_word['name']}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}操作已取消{Style.RESET_ALL}")
        sys.exit(0)
