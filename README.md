# 🩻 智链影语: 基于思维链大模型的X光影像自动诊断系统
基于思维链推理数据集监督微调的Janus-Pro-7B模型，用于放射学影像临床辅助诊断的医疗多模态大模型


本项目基于多模态大语言模型 **[Janus-CXR-7B](https://huggingface.co/ZYT0316/Janus-CXR-7B)**，通过轻量级的 Web 应用实现 X-Ray 图像的智能分析与诊断，具备中英文思维链生成、医学专业翻译等功能。

---

## 📦 安装依赖

确保你已安装 Python 3.10+ 和 pip，然后执行：

```bash
git clone https://github.com/YOUR_USERNAME/Janus-CXR-WebUI.git
cd Janus-CXR-WebUI
pip install -r requirements.txt

---

## 🚀 启动应用

streamlit run app.py
