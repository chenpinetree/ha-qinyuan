# 沁园净水机 Home Assistant 自定义集成 (Qinyuan Water Purifier)

本集成用于将**沁园（Qinyuan）智能净水机**（支持《沁园智联》App / 阿里云生活物联网平台接入的机型，例如 KRL3913 等）接入 Home Assistant。

## 功能特性

- 💧 **TDS 水质监测**：出水 TDS (ppm)、原水 TDS (ppm)
- 🧪 **滤芯寿命百分比监控**：
  - 复合滤芯寿命 (%)
  - 反渗透膜 (RO) 滤芯寿命 (%)
  - 炭棒滤芯寿命 (%)
- 📊 **用水数据**：累计制纯水量 (L)
- ⚙️ **工作状态**：设备当前运行状态（待机、制水、冲洗、缺水、满水等）
- 📶 **在线与制水状态**：在线状态 (Connectivity)、制水状态 (Purifying)

## 安装方式

### 方式一：通过 HACS / Marketplace 自定义存储库安装（推荐）

1. 打开 Home Assistant，进入 **Marketplace (市场 / HACS)**。
2. 点击右上角菜单按钮（三个点），选择 **自定义存储库 (Custom Repositories)**。
3. 存储库地址输入：`https://github.com/chenpinetree/ha-qinyuan`，类别选择 **集成 (Integration)**，点击添加。
4. 在市场中搜索 **沁园** 或 **Qinyuan**，点击下载安装。
5. 重启 Home Assistant。

### 方式二：手动安装

1. 下载本仓库，将 `custom_components/qinyuan` 目录复制到 Home Assistant 的 `config/custom_components/` 目录下。
2. 重启 Home Assistant。

## 配置说明

1. 在 Home Assistant 中进入 **设置 -> 设备与服务 -> 添加集成**。
2. 搜索 **沁园净水机 (Qinyuan Water Purifier)**。
3. 输入从《沁园智联》抓包获取的 `Authorization Token` 即可完成绑定。
