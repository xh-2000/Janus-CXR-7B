import os
import torch
import time
import streamlit as st
from PIL import Image
from transformers import AutoModelForCausalLM
from janus.models import MultiModalityCausalLM, VLChatProcessor
from janus.utils.io import load_pil_images
import http.client
import hashlib
import urllib.parse
import random
import json

# 页面设置
st.set_page_config(page_title="智链影语:基于思维链大模型的X光影像自动诊断系统", layout="wide")

# 自定义背景和样式
st.markdown("""
    <style>
    body {
        background-image: url("https://i.ibb.co/YRqdhfN/radiology-bg.jpg");
        background-size: cover;
        background-attachment: fixed;
    }
    .title {
        text-align: center;
        font-size: 36px;
        color: #FFFFFF;
        background: linear-gradient(to right, #2c3e50, #4ca1af);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .block-title {
        font-weight: bold;
        color: #004d99;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🩻 智链影语:基于思维链大模型的X光影像自动诊断系统</div>', unsafe_allow_html=True)

# 初始化状态
if 'model' not in st.session_state:
    st.session_state.model = None
if 'processor' not in st.session_state:
    st.session_state.processor = None
if 'tokenizer' not in st.session_state:
    st.session_state.tokenizer = None
if 'show_translation' not in st.session_state:
    st.session_state.show_translation = True
if 'translation_results' not in st.session_state:
    st.session_state.translation_results = {
        'thought_report': "",
        'report': "",
        'thought_conclusion': "",
        'conclusion': ""
    }
if 'last_translation_time' not in st.session_state:
    st.session_state.last_translation_time = 0

# 初始化结果状态
for key in ['thought_report', 'report', 'thought_conclusion', 'conclusion']:
    if key not in st.session_state:
        st.session_state[key] = ""

# 百度翻译的凭证 - 请在这里设置你的AppID和SecretKey
BAIDU_APPID = ""  # 替换为你的百度翻译AppID
BAIDU_SECRETKEY = ""  # 替换为你的百度翻译SecretKey
MEDICAL_DOMAIN = "senimed"  # 使用医学领域翻译

system_prompt = """You are an experienced and meticulous radiologist. Based on the X-ray images I provide, think through the process and write a radiology report for me. Then, based on the radiology report you have written, think through the process and write a radiology conclusion.\n\nPlease strictly follow the sequence of thought:\n1. Radiology report thought process\n2. Radiology report\n3. Radiology conclusion thought process\n4. Radiology conclusion\n\nEnsure that both the radiology report and conclusion are derived from your thought process. The content should be filled in the designated format, with attention to observed phenomena and awareness of key details, simulating your thought process while interpreting the X-ray images. Additionally, your language should be natural, fluent, professional, and concise."""
question = """Please analyze this X-ray image and write a radiology report, then summarize a radiology conclusion based on the report.\n\nEnsure your analysis is rigorous, professional, and concise, following a step-by-step reasoning process in the following order:\n1. Analyze the X-ray image.\n2. Write the radiology report.\n3. Analyze the radiology report.\n4. Write the radiology conclusion.\n\nYour report should adhere to a professional radiology format and be written in a natural, fluent manner."""

# 百度翻译函数 - 使用http.client和医学领域翻译
def translate_text(text, from_lang='en', to_lang='zh'):
    """使用百度翻译API翻译文本，使用医学领域专业翻译"""
    if not text.strip():
        return ""
    
    # 处理API并发限制 - 确保至少间隔1.1秒
    current_time = time.time()
    elapsed = current_time - st.session_state.last_translation_time
    if elapsed < 1.1:  # 稍微超过1秒以确保安全
        sleep_time = 1.1 - elapsed
        time.sleep(sleep_time)
    
    st.session_state.last_translation_time = time.time()  # 更新最后翻译时间
    
    # 生成签名
    salt = random.randint(32768, 65536)
    sign_str = f"{BAIDU_APPID}{text}{salt}{MEDICAL_DOMAIN}{BAIDU_SECRETKEY}"
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    
    # 构建URL
    base_url = "/api/trans/vip/fieldtranslate"
    params = {
        'appid': BAIDU_APPID,
        'q': text,
        'from': from_lang,
        'to': to_lang,
        'salt': salt,
        'domain': MEDICAL_DOMAIN,
        'sign': sign
    }
    query_string = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{query_string}"
    
    try:
        # 创建HTTP连接
        conn = http.client.HTTPConnection('api.fanyi.baidu.com')
        conn.request("GET", full_url)
        
        # 获取响应
        response = conn.getresponse()
        result_all = response.read().decode("utf-8")
        result = json.loads(result_all)
        
        # 处理结果
        if 'trans_result' in result:
            # 合并所有翻译结果
            return '\n'.join([item['dst'] for item in result['trans_result']])
        elif 'error_code' in result:
            error_msg = f"翻译错误 {result['error_code']}: {result['error_msg']}"
            st.error(error_msg)
            return f"[翻译失败] {text}"
        else:
            st.error(f"未知翻译错误: {result}")
            return f"[翻译失败] {text}"
            
    except Exception as e:
        st.error(f"翻译请求失败: {str(e)}")
        return f"[翻译失败] {text}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 布局区域划分
left_col, center_col, right_col = st.columns([1.5, 1, 2])

with left_col:
    st.markdown("#### 📂 模型加载")
    model_path = st.text_input("🔍 模型路径", value="./checkpoints/Janus-CXR-7B/")
    if st.button("🚀 加载模型"):
        with st.spinner("加载中..."):
            try:
                st.session_state.processor = VLChatProcessor.from_pretrained(model_path)
                st.session_state.tokenizer = st.session_state.processor.tokenizer
                st.session_state.model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
                st.session_state.model = st.session_state.model.to(torch.bfloat16).cuda().eval()
                st.success("✅ 模型加载成功")
            except Exception as e:
                st.error(f"❌ 加载失败：{e}")

    st.markdown("#### 🖼️ 图像上传")
    uploaded_file = st.file_uploader("上传X光图像", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="📸 上传图像", use_container_width=True)

with center_col:
    st.markdown("#### 🧠 推理操作")
    
    # 将翻译开关移到中间栏
    st.session_state.show_translation = st.checkbox("显示中文翻译", value=st.session_state.show_translation, key="translation_toggle")
    
    if st.button("🧪 开始推理"):
        if uploaded_file is None:
            st.warning("⚠️ 请先上传图像")
        elif st.session_state.model is None:
            st.warning("⚠️ 请先加载模型")
        else:
            with st.spinner("推理中..."):
                start_time = time.time()
                image_path = f"/tmp/{uploaded_file.name}"
                image.save(image_path)

                conversation = [
                    {"role": "<|System|>", "content": system_prompt},
                    {"role": "<|User|>", "content": f"<image_placeholder>\n{question}", "images": [image_path]},
                    {"role": "<|Assistant|>", "content": ""},
                ]
                pil_images = load_pil_images(conversation)
                inputs = st.session_state.processor(conversations=conversation, images=pil_images, force_batchify=True).to(st.session_state.model.device)
                inputs_embeds = st.session_state.model.prepare_inputs_embeds(**inputs)

                outputs = st.session_state.model.language_model.generate(
                    inputs_embeds=inputs_embeds,
                    attention_mask=inputs.attention_mask,
                    pad_token_id=st.session_state.tokenizer.eos_token_id,
                    bos_token_id=st.session_state.tokenizer.bos_token_id,
                    eos_token_id=st.session_state.tokenizer.eos_token_id,
                    max_new_tokens=4096,
                    do_sample=True,
                    temperature=0.3,
                    top_k=20,
                    top_p=0.7,
                    repetition_penalty=1.05,
                    use_cache=True
                )
                answer = st.session_state.tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)

                def extract_block(start, end):
                    s, e = answer.find(start), answer.find(end)
                    return answer[s + len(start):e].strip() if s != -1 and e != -1 and e > s else ""

                st.session_state.thought_report = extract_block("### Thought Process for the Report:", "### Report:")
                st.session_state.report = extract_block("### Report:", "### Thought Process for the Conclusion:")
                st.session_state.thought_conclusion = extract_block("### Thought Process for the Conclusion:", "### Conclusion:")
                st.session_state.conclusion = answer.split("### Conclusion:")[-1].strip()
                

                # 翻译结果 - 单独翻译每个部分
                if st.session_state.show_translation:
                    with st.spinner("医学翻译中..."):
                        # 翻译报告思维
                        st.session_state.translation_results['thought_report'] = translate_text(st.session_state.thought_report)
                        
                        # 翻译放射报告
                        st.session_state.translation_results['report'] = translate_text(st.session_state.report)
                        
                        # 翻译结论思维
                        st.session_state.translation_results['thought_conclusion'] = translate_text(st.session_state.thought_conclusion)
                        
                        # 翻译最终结论
                        st.session_state.translation_results['conclusion'] = translate_text(st.session_state.conclusion)
                else:
                    # 如果不显示翻译，清空翻译结果
                    for key in st.session_state.translation_results:
                        st.session_state.translation_results[key] = ""

                end_time = time.time()
                st.success(f"✅ 推理完成，用时 {end_time - start_time:.2f} 秒")

    if st.button("🧹 清空推理内容"):
        for key in ['thought_report', 'report', 'thought_conclusion', 'conclusion']:
            st.session_state[key] = ""
        for key in st.session_state.translation_results:
            st.session_state.translation_results[key] = ""
        st.session_state.last_translation_time = 0  # 重置翻译时间
        st.success("🧼 推理内容已清空")

with right_col:
    if st.session_state.report:
        st.markdown("#### 🧠 思维链展示")
        
        # 显示报告思维
        if st.session_state.show_translation and st.session_state.translation_results['thought_report']:
            st.text_area("🧩 报告思维", value=st.session_state.translation_results['thought_report'], height=150)
        else:
            st.text_area("🧩 报告思维", value=st.session_state.thought_report, height=150)
        
        # 显示结论思维
        if st.session_state.show_translation and st.session_state.translation_results['thought_conclusion']:
            st.text_area("🧩 结论思维", value=st.session_state.translation_results['thought_conclusion'], height=150)
        else:
            st.text_area("🧩 结论思维", value=st.session_state.thought_conclusion, height=150)
        
        st.markdown("#### 📑 推理结果展示")
        
        # 显示放射报告
        if st.session_state.show_translation and st.session_state.translation_results['report']:
            st.text_area("📋 放射报告", value=st.session_state.translation_results['report'], height=150)
        else:
            st.text_area("📋 放射报告", value=st.session_state.report, height=150)
        
        # 显示最终结论
        if st.session_state.show_translation and st.session_state.translation_results['conclusion']:
            st.text_area("🏁 最终结论", value=st.session_state.translation_results['conclusion'], height=100)
        else:
            st.text_area("🏁 最终结论", value=st.session_state.conclusion, height=100)
