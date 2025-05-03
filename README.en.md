<!-- ESP-SR-Model-Tool -->
<h1 align="center">ESP-SR-Model-Tool</h1>

<p align="center">
  <img src="https://img.shields.io/badge/PlatformIO-FF6F00?style=flat&logo=platformio&logoColor=white" alt="PlatformIO">
  <img src="https://img.shields.io/badge/Arduino-00979D?style=flat&logo=arduino&logoColor=white" alt="Arduino">
  <br>
  <a href="https://opensource.org/licenses/Apache2.0"><img src="https://img.shields.io/badge/License-Apache2.0-yellow.svg" alt="License: Apache2.0"></a>
  <img src="https://img.shields.io/badge/ESP32-Compatible-brightgreen" alt="ESP32">
</p>

A speech recognition model management tool for ESP32 series chips, helping developers easily configure, generate, and flash wake word models.

English | [中文](./README.md)

![Demo](assets/README/image.png)

ESP-SR-Model-Tool is an easy-to-use ESP32 speech recognition model configuration tool that helps you quickly select, generate, and flash various wake word models to your ESP32 device. No need to manually configure complex parameters, just a few simple steps to complete the deployment of wake words.

### ✨ Features

- 📋 **Intuitive Interactive Interface** - Easily select wake words and configurations through command-line interaction
- 🔊 **Rich Wake Word Support** - Supports all official wake words in WakeNet9 and WakeNet9s
- 📊 **Grouped Display** - Wake words are grouped by categories such as Chinese, English, etc., for easy selection
- 🔍 **Smart Partition Table Parsing** - Automatically scans and parses partition tables in the project to get the correct address
- 📝 **Dynamic Configuration Generation** - Automatically generates sdkconfig configuration files
- 📈 **Real-time Progress Display** - Shows progress during flashing with animated progress bars
- 🔌 **Multi-platform Support** - Compatible with Windows, Linux, and macOS systems
- 🌐 **Speech Recognition Support** - Optional configuration of speech recognition models (MultiNet)
- 🔄 **TTS Data Flashing** - Supports flashing TTS voice synthesis data

### 🛠️ Installation and Dependencies

Before using this tool, please make sure you have installed the required Python dependencies:

```bash
# Clone the repository
git clone https://github.com/yourusername/esp-sr-model-tool.git
cd esp-sr-model-tool

# Install dependencies
pip install -r requirements.txt

# Run the tool
python main.py

```

You will also need:

1. ESP-IDF or Arduino ESP32 development environment installed
2. ESP-SR library (needs to be placed in the wake-word-tool/esp-sr directory)
3. esptool installed (`pip install esptool`)

### 🚀 Usage

#### Interactive Usage (Recommended)

1. Make sure your ESP32 is connected to your computer via USB
2. Run the following command to start the tool:

```bash
cd wake-word-tool
python main.py
```

3. Follow the interactive interface prompts:
   - Select wake word category (WakeNet9 or WakeNet9s)
   - Select specific wake word
   - Select speech recognition model (optional)
   - Select partition table file
   - Select serial port device
   - Wait for model generation and flashing to complete

#### Usage Effects

![Select Wake Word](assets/README/image-1.png)
![Select TTS Model](assets/README/image-2.png)

#### Command Line Arguments

Advanced users can directly specify configurations through command line arguments without interactive selection:

```bash
python main.py -c xiaoaitongxue.sdkconfig -p COM3 -b 2000000 -t -y
```

Available command line arguments:

| Parameter | Description |
| ---- | ---- |
| `-c`, `--config` | Specify wake word configuration file path (.sdkconfig) |
| `-p`, `--port` | Specify serial port device (e.g., COM3 or /dev/ttyUSB0) |
| `-b`, `--baud` | Specify baud rate (default: 2000000) |
| `-t`, `--tts` | Flash TTS voice data simultaneously |
| `-y`, `--yes` | Automatically confirm all operations, no user confirmation required |
| `-a`, `--address` | Directly specify model flashing address (e.g., 0x710000) |

For example, to automatically flash the "XiaoAi Tongxue" wake word and TTS data simultaneously:

```bash
python main.py -c xiaoaitongxue.sdkconfig -p COM3 -t -y
```

### 📋 Supported Wake Words

The tool supports all officially provided ESP wake words, including:

**Chinese Wake Words**:

- Ni Hao Xiao Zhi, Ni Hao Xiao Xin, Xiao Ai Tongxue
- Xiao Mei Tongxue, Miao Miao Tongxue, Xiao Long Xiao Long
- Xiao Yu Tongxue, Xiao Ming Tongxue, Xiao Kang Tongxue
- Xiao Bin Xiao Bin, Xiao Ya Xiao Ya, Li Nai Ban
- Xiao Su Rou, Xiao Jian Xiao Jian, Xiao Te Xiao Te
- And more...

**English/Hi Series Wake Words**:

- Hi ESP, Hi Espressif, Hi Jason
- Hi M Five, Hi Wally, Hi Xiao Xing
- Hi Miao Miao, Hi Lily, Hi Taili
- Hi Xiao Wu, and more...

**Other Wake Words**:

- Alexa, Jarvis, Computer
- Hey Willow, Sophia, Mycroft
- Hey Printer, Hi Joy, Hey Wanda
- Astrolabe, and more...

### 📄 Partition Table Configuration

The tool will automatically search for partition table files in the project directory and parse out the correct model and voice data flashing addresses. A typical partition table entry example:

```
# Name, Type, SubType, Offset, Size
nvs,data,nvs,0x9000,0x6000
phy_init,data,phy,0xf000,0x1000
factory,app,factory,0x10000,1M
model,data,spiffs,0x710000,0x5E0000
voice_data,data,fat,0xCF0000,0x300000
```

The tool will automatically use the offset of the model partition (0x710000) as the flashing address.

If the partition table cannot be found or there is no model partition in the partition table, the tool will use the default address (0x710000).

### ❓ Frequently Asked Questions

1. **How to get the ESP-SR library?**
   - Download from Espressif's official GitHub: [esp-sr](https://github.com/espressif/esp-sr)
   - Or use the ESP-SR zip package provided by this project

2. **Cannot find wake word configuration file?**
   - The new version of the tool will automatically generate configuration files, no need to create manually
   - If you need to use an existing configuration, ensure the file extension is `.sdkconfig`
   - Check if the configuration file contains the correct wake word configuration items

3. **Encountered file encoding errors?**
   - The tool supports multiple encoding formats (UTF-8, GBK, GB2312, Latin1, CP1252)
   - If there's an issue, open the sdkconfig file with Notepad and save it as UTF-8 encoding

4. **Cannot find COM port?**
   - Check if the device connection is normal
   - Confirm that the driver is correctly installed
   - Use the `-p` parameter to manually specify the port

5. **Model generation failed?**
   - Confirm that the esp-sr directory structure is correct
   - Check if the movemodel.py script exists in the esp-sr/model directory

6. **Flashing failed?**
   - Try lowering the baud rate (`-b 115200`)
   - Some ESP32s need to manually enter download mode (hold BOOT button and then press RST)
   - Check if the driver is correctly installed

### 🤝 Contribution

Contributions of code, issue reports, or improvement suggestions are welcome! Please follow these steps:

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### 📜 License

This project is licensed under the Apache License - see the [LICENSE](LICENSE) file for details

---
