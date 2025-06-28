# 🩻 智链影语：基于思维链大模型的 X 光影像智能诊断系统

**Janus-CXR-7B** 是我们团队自主训练的医学多模态大语言模型，基于 30,000 例 MIMIC-CXR 胸部 X 光影像及其对应报告与结论构建思维链推理数据集，采用 Janus-Pro-7B 作为基础模型，进行监督微调优化而成。

本项目提供一个轻量级 Web 应用，将 Janus-CXR-7B 部署于前端界面，实现以下功能：

- 🧠 多轮中英文思维链生成  
- 📜 医学放射学报告自动撰写  
- 🗣️ 医学术语中英互译  
- 🩺 智能诊断结论生成与病灶分类辅助  

---

## 📦 安装依赖

确保你已安装 Python 3.10+ 和 Conda，并且拥有至少 17GB 显存（推荐 20GB）。


### 克隆项目代码
```bash
git clone https://github.com/xh-2000/Janus-CXR-7B.git
```

### 进入项目目录
```bash
cd Janus-CXR-7B
```

### 创建 Conda 虚拟环境
```bash
conda create -n Janus-CXR-7B python=3.10 -y
```

```bash
conda activate Janus-CXR-7B
```

### 安装依赖
```bash
pip install -r requirements.txt
```

---

## 💾 下载模型权重（手动）

请前往 Hugging Face 模型仓库下载我们训练的模型权重：

👉 模型地址：https://huggingface.co/ZYT0316/Janus-CXR-7B

下载后，将模型权重解压，并放置到以下目录（若无请手动创建）：

```bash
./checkpoints/Janus-CXR-7B/
```

## 🚀 启动应用
在启动之前您应当修改app.py文件的69，70行百度翻译API的相关内容为自己的API以保证可以顺利翻译结果。

修改app.py文件144行模型路径为Janus-CXR-7B的路径

使用 Streamlit 启动 Web 前端应用：
```bash
streamlit run app.py
```

## 📫 联系我们

如需合作、模型授权或进一步交流，欢迎联系：

📧 邮箱：zyt20000316@mail.nwpu.edu.cn

🧑‍💻 项目作者：智链影语团队

🌐 GitHub: https://github.com/xh-2000

## 📜 许可协议
本项目采用 MIT License 开源，代码部分可自由使用和修改。
模型权重部分仅限学术研究用途，禁止任何形式的商业化应用，如需商用，请联系作者获得授权。

版权所有 © 2025 智链影语团队. 保留所有权利。
