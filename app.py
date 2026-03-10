import streamlit as st
import os
import base64
import time
import tempfile
import struct
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
import requests

from utils.image_processor import validate_image, get_image_info
from utils.mock_generator import MockGenerator, LoadingMessages
from utils.meshy_api import MeshyAPI

import textwrap

# 加载 secrets - 使用 Meshy API
try:
    MESHY_API_KEY = st.secrets["meshy"]["api_key"]
except Exception:
    MESHY_API_KEY = None

st.set_page_config(
    page_title="Snap3D - 免建模图像转3D助手",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');
    
    :root {
        --bg-color: #070b14;
        --card-bg: rgba(255, 255, 255, 0.02);
        --primary-cyan: #00d1d6;
        --primary-purple: #7c3aed;
        --text-main: #EAFBFF;
        --text-sub: #A7B3C2;
        --accent-glow: 0 0 10px rgba(0, 209, 214, 0.5);
    }

    /* 全局重置与背景 */
    .stApp {
        background-color: var(--bg-color);
        background-image:
            radial-gradient(white, rgba(255,255,255,.2) 2px, transparent 40px),
            radial-gradient(white, rgba(255,255,255,.15) 1px, transparent 30px),
            radial-gradient(white, rgba(255,255,255,.1) 2px, transparent 40px),
            linear-gradient(rgba(0, 209, 214, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 209, 214, 0.03) 1px, transparent 1px);
        background-size: 550px 550px, 350px 350px, 250px 250px, 40px 40px, 40px 40px;
        color: var(--text-main);
        font-family: 'Inter', sans-serif;
        font-size: 20px;
    }
    
    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }

    /* Section Label Style */
    .section-label {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        color: var(--text-sub);
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1.2rem;
        letter-spacing: 1px;
    }
    .section-label::before {
        content: '';
        display: block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: var(--text-sub);
    }
    .section-label.preview-label::before {
        background-color: var(--primary-purple);
        box-shadow: 0 0 10px var(--primary-purple);
    }

    /* Tabs 优化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
        padding: 0;
        border: none;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 50px;
        color: var(--text-sub);
        padding: 14px 32px;
        font-family: 'Inter', sans-serif;
        font-weight: 600; /* 加粗 */
        font-size: 1.6rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        flex-grow: 0;
        min-width: 180px; /* 稍微加宽 */
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #00d1d6, #7c3aed) !important;
        border: none !important;
        color: #fff !important;
        box-shadow: 0 4px 15px rgba(0, 209, 214, 0.3);
        font-weight: 600;
    }
    
    /* 上传区域优化 - 增大空间 */
    .stFileUploader > div,
    .stFileUploader [data-testid="stFileUploaderDropzone"] {
        background: rgba(11, 15, 20, 0.88) !important;
        border: 2px dashed rgba(0, 209, 214, 0.75) !important;
        border-radius: 20px;
        padding: 7rem 2.2rem !important;
        min-height: 480px;
        box-shadow: 0 0 24px rgba(0, 209, 214, 0.08) inset;
    }
    .stFileUploader > div:hover,
    .stFileUploader [data-testid="stFileUploaderDropzone"]:hover {
        background: rgba(11, 18, 32, 0.82) !important;
        box-shadow: 0 0 34px rgba(0, 209, 214, 0.14) inset;
    }
    .stFileUploader [data-testid="stFileUploaderDropzone"] * {
        color: #fff !important;
        opacity: 1 !important;
    }
    .stFileUploader [data-testid="stFileUploaderDropzone"] div,
    .stFileUploader [data-testid="stFileUploaderDropzone"] section {
        background: transparent !important;
    }
    .stFileUploader [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p {
        color: rgba(234, 240, 247, 0.92) !important;
    }
    .stFileUploader [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] small {
        color: rgba(167, 179, 194, 0.9) !important;
    }
    .stFileUploader [data-testid="stFileUploaderDropzone"] button,
    .stFileUploader [data-testid="stFileUploaderDropzone"] a[role="button"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        color: #fff !important;
        border-radius: 14px !important;
        padding: 0.7rem 1.1rem !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
    }
    .stFileUploader [data-testid="stFileUploaderDropzone"] button:hover,
    .stFileUploader [data-testid="stFileUploaderDropzone"] a[role="button"]:hover {
        background: rgba(0, 209, 214, 0.18) !important;
        border-color: rgba(0, 209, 214, 0.45) !important;
    }
    .stFileUploader [data-testid="stFileUploaderDropzone"] small,
    .stFileUploader div[data-testid="stMarkdownContainer"] p small {
        color: var(--text-sub) !important;
        font-size: 1.1rem !important;
    }
    .stFileUploader div[data-testid="stMarkdownContainer"] p {
        font-size: 1.4rem !important;
        font-weight: 650 !important;
        color: #fff !important;
    }
    .stFileUploader section {
        background: transparent !important;
    }
    .stFileUploader section > div {
        background: transparent !important;
        border: none !important;
    }

    /* 兼容不同 Streamlit 版本：强制上传拖放区深色底 + 高对比文字 */
    div[data-testid="stFileUploaderDropzone"],
    section[data-testid="stFileUploaderDropzone"],
    div[data-testid="stFileUploadDropzone"],
    section[data-testid="stFileUploadDropzone"] {
        background: rgba(43, 47, 54, 0.92) !important;
        border: 1px solid rgba(191, 197, 206, 0.55) !important;
        border-top: 2px solid rgba(0, 209, 214, 0.65) !important;
        border-radius: 18px !important;
        box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.22) inset, 0 10px 30px rgba(0, 0, 0, 0.28);
    }
    div[data-testid="stFileUploaderDropzone"] *,
    section[data-testid="stFileUploaderDropzone"] *,
    div[data-testid="stFileUploadDropzone"] *,
    section[data-testid="stFileUploadDropzone"] * {
        background: transparent !important;
    }
    div[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"],
    section[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"],
    div[data-testid="stFileUploadDropzone"] [data-testid*="DropzoneInstructions"],
    section[data-testid="stFileUploadDropzone"] [data-testid*="DropzoneInstructions"] {
        color: rgba(234, 240, 247, 0.92) !important;
    }
    div[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] *,
    section[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] *,
    div[data-testid="stFileUploadDropzone"] [data-testid*="DropzoneInstructions"] *,
    section[data-testid="stFileUploadDropzone"] [data-testid*="DropzoneInstructions"] * {
        color: rgba(234, 240, 247, 0.9) !important;
        font-weight: 550 !important;
    }
    div[data-testid="stFileUploaderDropzone"] small,
    section[data-testid="stFileUploaderDropzone"] small,
    div[data-testid="stFileUploadDropzone"] small,
    section[data-testid="stFileUploadDropzone"] small {
        color: rgba(167, 179, 194, 0.9) !important;
    }
    div[data-testid="stFileUploaderDropzone"] svg,
    section[data-testid="stFileUploaderDropzone"] svg,
    div[data-testid="stFileUploadDropzone"] svg,
    section[data-testid="stFileUploadDropzone"] svg {
        color: rgba(125, 211, 252, 0.85) !important;
    }
    div[data-testid="stFileUploaderDropzone"] button,
    section[data-testid="stFileUploaderDropzone"] button,
    div[data-testid="stFileUploadDropzone"] button,
    section[data-testid="stFileUploadDropzone"] button,
    div[data-testid="stFileUploaderDropzone"] a[role="button"],
    section[data-testid="stFileUploaderDropzone"] a[role="button"],
    div[data-testid="stFileUploadDropzone"] a[role="button"],
    section[data-testid="stFileUploadDropzone"] a[role="button"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        color: rgba(234, 240, 247, 0.95) !important;
        border-radius: 14px !important;
    }

    /* 提示条样式 */
    .tip-banner {
        background: rgba(251, 191, 36, 0.1);
        border: 1px solid rgba(251, 191, 36, 0.2);
        border-radius: 10px;
        padding: 10px 14px;
        color: #fbbf24;
        font-size: 0.98rem;
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 0.7rem 0 1.0rem;
        background: linear-gradient(90deg, rgba(251, 191, 36, 0.05), transparent);
        flex-wrap: wrap;
    }
    .tip-banner .tip-icon {
        flex: 0 0 auto;
        line-height: 1;
    }
    .tip-banner .tip-text {
        flex: 1 1 320px;
        line-height: 1.45;
        min-width: 0;
    }

    /* 按钮样式 */
    div.stButton > button {
        background: linear-gradient(90deg, #00d1d6, #8b3dff);
        border: none;
        color: white;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.4rem;
        padding: 1.2rem 3rem;
        border-radius: 50px;
        width: 100%;
        box-shadow: 0 4px 20px rgba(124, 58, 237, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 209, 214, 0.5);
    }
    div.stButton > button:active {
        transform: translateY(1px);
    }
    div.stButton > button:disabled {
        background: #1e293b;
        color: #64748b;
        box-shadow: none;
        cursor: not-allowed;
    }

    /* 3D 预览面板 - 固定高度 */
    .preview-panel {
        position: relative;
        background: #0b1220;
        border-radius: 20px;
        height: 550px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 0 50px rgba(0, 0, 0, 0.5) inset;
    }
    
    .bracket {
        position: absolute;
        width: 40px;
        height: 40px;
        border: 2px solid var(--primary-cyan);
        pointer-events: none;
        box-shadow: 0 0 10px var(--primary-cyan);
    }
    .bracket-tl { top: 20px; left: 20px; border-right: none; border-bottom: none; border-radius: 12px 0 0 0; }
    .bracket-bl { bottom: 20px; left: 20px; border-right: none; border-top: none; border-radius: 0 0 0 12px; }

    /* 浮动工具栏 */
    .floating-tools {
        position: absolute;
        right: 20px;
        top: 50%;
        transform: translateY(-50%);
        display: flex;
        flex-direction: column;
        gap: 10px;
        z-index: 100;
    }
    .tool-btn {
        width: 50px;
        height: 50px;
        background: rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--primary-cyan);
        cursor: pointer;
        backdrop-filter: blur(5px);
        transition: all 0.2s;
    }
    .tool-btn:hover {
        background: rgba(0, 209, 214, 0.2);
        box-shadow: 0 0 10px rgba(0, 209, 214, 0.3);
    }

    /* 输入框 - 深色背景白字 */
    .stTextInput input,
    .stTextArea textarea,
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="input"] input {
        background-color: rgba(11, 15, 20, 0.88) !important;
        border: 2px solid rgba(255, 255, 255, 0.16) !important;
        color: #ffffff !important;
        font-size: 1.2rem;
        border-radius: 14px;
        padding: 14px 18px;
        box-shadow: 0 1px 0 rgba(0, 0, 0, 0.15);
    }
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder,
    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder,
    div[data-baseweb="textarea"] textarea::placeholder,
    div[data-baseweb="input"] input::placeholder {
        color: rgba(234, 240, 247, 0.45) !important;
    }
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus,
    div[data-baseweb="textarea"] textarea:focus,
    div[data-baseweb="input"] input:focus {
        border-color: rgba(0, 209, 214, 0.75) !important;
        box-shadow: 0 0 0 2px rgba(0, 209, 214, 0.12);
        outline: none !important;
    }
    div[data-testid="stTextArea"] [data-testid="stWidgetLabel"] + div,
    div[data-testid="stTextInput"] [data-testid="stWidgetLabel"] + div,
    div[data-baseweb="textarea"],
    div[data-baseweb="input"] {
        background: transparent !important;
    }
    div[data-testid="stTextArea"] [data-testid="InputInstructions"],
    div[data-testid="stTextInput"] [data-testid="InputInstructions"] {
        color: rgba(234, 240, 247, 0.55) !important;
    }

    /* Selectbox */
    div[data-baseweb="select"] > div,
    .stSelectbox > div > div {
        background-color: rgba(11, 15, 20, 0.88) !important;
        border: 2px solid rgba(255, 255, 255, 0.22) !important;
        box-shadow: 0 0 0 1px rgba(0, 209, 214, 0.08) inset;
    }
    div[data-baseweb="select"] *,
    .stSelectbox * {
        color: #fff !important;
        opacity: 1 !important;
    }
    
    /* 下拉菜单 */
    div[data-baseweb="popover"] * {
        background-color: transparent !important;
    }
    div[data-baseweb="popover"] div[role="listbox"],
    div[role="listbox"][data-baseweb="menu"],
    ul[data-baseweb="menu"],
    div[data-baseweb="menu"] {
        background: rgba(11, 15, 20, 0.98) !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.55) !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    
    /* 下拉选项 */
    div[role="option"],
    li[role="option"],
    li[data-baseweb="option"] {
        background: rgba(11, 15, 20, 0.98) !important;
        color: #EAF0F7 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1.15rem !important;
        font-weight: 500 !important;
        opacity: 1 !important;
        box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.14);
    }
    div[role="option"] *,
    li[role="option"] *,
    li[data-baseweb="option"] * {
        color: #fff !important;
        opacity: 1 !important;
    }
    div[role="option"]:hover,
    li[role="option"]:hover,
    li[data-baseweb="option"]:hover,
    div[role="option"][aria-selected="true"],
    li[role="option"][aria-selected="true"],
    li[data-baseweb="option"][aria-selected="true"] {
        background: rgba(16, 26, 42, 0.98) !important;
        color: #7DD3FC !important;
    }
    div[data-baseweb="menu"] [role="option"][aria-selected="true"],
    ul[data-baseweb="menu"] [role="option"][aria-selected="true"],
    div[role="listbox"] [role="option"][aria-selected="true"] {
        background: rgba(16, 26, 42, 0.98) !important;
        color: #7DD3FC !important;
    }
    div[data-baseweb="menu"] [role="option"][aria-selected="true"] *,
    ul[data-baseweb="menu"] [role="option"][aria-selected="true"] *,
    div[role="listbox"] [role="option"][aria-selected="true"] * {
        color: #7DD3FC !important;
    }

    /* 文本颜色修正 */
    h1, h2, h3, p, span, div { color: var(--text-main); }
    .stMarkdown p { font-size: 1.2rem; line-height: 1.7; }
    
    /* 标签文字 (Tab Labels, Input Labels) */
    label, .stTextInput label, .stTextArea label, .stSelectbox label {
        font-size: 1.6rem !important;
        color: var(--text-sub) !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
    }

    /* 动画定义 */
    @keyframes spin { 
        0% { transform: rotate(0deg); } 
        100% { transform: rotate(360deg); } 
    }
</style>
"""

if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'generated_stl' not in st.session_state:
    st.session_state.generated_stl = None
if 'generated_glb' not in st.session_state:
    st.session_state.generated_glb = None
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False
if 'last_uploaded_file_id' not in st.session_state:
    st.session_state.last_uploaded_file_id = None
if 'model_urls' not in st.session_state:
    st.session_state.model_urls = {}

def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Cyberpunk Header - Centered & Enlarged
    st.markdown(textwrap.dedent("""
  <div class="cyber-header">
    <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
      <svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 0 10px rgba(0, 209, 214, 0.3));">
        <defs>
          <linearGradient id="palette_gradient" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#00d1d6" />
            <stop offset="100%" stop-color="#7c3aed" />
          </linearGradient>
        </defs>
        <path d="M12 3C6.48 3 2 7.48 2 13C2 18.52 6.48 23 12 23C12.55 23 13 22.55 13 22C13 21.45 12.55 21 12 21C11.45 21 11 20.55 11 20C11 19.45 11.45 19 12 19C13.66 19 15 17.66 15 16V15C15 14.45 15.45 14 16 14H18C20.21 14 22 12.21 22 10C22 6.13 17.52 3 12 3ZM6.5 13C5.67 13 5 12.33 5 11.5C5 10.67 5.67 10 6.5 10C7.33 10 8 10.67 8 11.5C8 12.33 7.33 13 6.5 13ZM9.5 8C8.67 8 8 7.33 8 6.5C8 5.67 8.67 5 9.5 5C10.33 5 11 5.67 11 6.5C11 7.33 10.33 8 9.5 8ZM14.5 8C13.67 8 13 7.33 13 6.5C13 5.67 13.67 5 14.5 5C15.33 5 16 5.67 16 6.5C16 7.33 15.33 8 14.5 8ZM17.5 13C16.67 13 16 12.33 16 11.5C16 10.67 16.67 10 17.5 10C18.33 10 19 10.67 19 11.5C19 12.33 18.33 13 17.5 13Z" fill="url(#palette_gradient)" />
      </svg>
      <h1 style="font-family: 'Inter', sans-serif; font-weight: 900; font-size: 4rem; color: #fff; margin: 0; padding: 0; letter-spacing: -2px; line-height: 1.2;">
        Snap<span style="color: #00d1d6;">3D</span>
      </h1>
    </div>
    <p style="font-family: 'Inter', sans-serif; color: #94a3b8; font-size: 1.2rem; margin-top: 12px; font-weight: 500; letter-spacing: 1px;">
      一键3D建模生成
    </p>
  </div>
  """), unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        # 输入 Section Label
        st.markdown('<div class="section-label">输入</div>', unsafe_allow_html=True)

        # 创建 Tabs
        tab_image, tab_text = st.tabs(["🖼️ 图片转3D", "📝 文字转3D"])
        
        # ==================== Image to 3D Tab ====================
        with tab_image:
            # 上传区域
            uploaded_file = st.file_uploader(
                "拖放图片或点击上传",
                type=['png', 'jpg', 'jpeg', 'webp'],
                help="支持 PNG · JPG · WEBP · 最大 20MB",
                key="image_uploader"
            )
            
            # 提示条
            st.markdown(textwrap.dedent("""
            <div class="tip-banner">
              <span class="tip-icon" style="font-size: 1.2rem;">⚠️</span>
              <span class="tip-text">建议使用清晰的单物体照片，白色或纯色背景效果最佳</span>
            </div>
            """), unsafe_allow_html=True)
            
            # 实际逻辑处理 (文件验证等)
            if uploaded_file is not None:
                # 检查是否是新文件
                current_file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                
                if 'last_uploaded_file_id' not in st.session_state or st.session_state.last_uploaded_file_id != current_file_id:
                    st.session_state.last_uploaded_file_id = current_file_id
                    st.session_state.uploaded_file = uploaded_file
                    st.session_state.generation_complete = False
                    st.session_state.generated_stl = None
                    st.session_state.generated_glb = None
                    st.session_state.model_urls = {}
                    st.session_state.is_generating = False
                
                is_valid, message = validate_image(uploaded_file)
                
                if is_valid:
                    # 预览图 (可选，如果想保持简洁可以不显示，或者显示在右侧)
                    pass 
                else:
                    st.error("❌ " + message)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            generate_image_btn = st.button(
                "✨ 图片转 3D ✨",
                disabled=(uploaded_file is None or st.session_state.is_generating),
                use_container_width=True,
                key="btn_image_gen"
            )

        # ==================== Text to 3D Tab ====================
        with tab_text:
            text_prompt = st.text_area(
                "描述你想生成的 3D 模型",
                placeholder="例如：一只戴着巫师帽的可爱卡通小猫，坐在魔法书上...",
                height=280,
                key="text_prompt_input"
            )
            
            # 提示条
            st.markdown(textwrap.dedent("""
            <div class="tip-banner">
              <span style="font-size: 1.2rem;">💡</span>
              <span>提示：描述越详细，生成的模型越准确。支持中英文。</span>
            </div>
            """), unsafe_allow_html=True)
            
            st.markdown('<p style="font-size: 1.4rem; color: #A7B3C2; margin-bottom: 0.75rem; font-weight: 600;">🎨 艺术风格</p>', unsafe_allow_html=True)
            st.markdown('<p style="font-size: 1.1rem; color: rgba(167, 179, 194, 0.8); margin-bottom: 0.5rem;">Meshy-6 自动优化风格</p>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            generate_text_btn = st.button(
                "✨ 文字转 3D ✨",
                disabled=(not text_prompt or st.session_state.is_generating),
                use_container_width=True,
                key="btn_text_gen"
            )

        # 处理生成触发逻辑
        if generate_image_btn and uploaded_file is not None:
            if not MESHY_API_KEY:
                st.error("❌ Meshy API Key Not Configured")
            else:
                st.session_state.is_generating = True
                st.session_state.generation_mode = "image" # 记录模式
                st.session_state.generation_complete = False
                st.session_state.generated_stl = None
                st.session_state.generated_glb = None
                st.session_state.model_urls = {}
                st.rerun()
        
        if generate_text_btn and text_prompt:
            if not MESHY_API_KEY:
                st.error("❌ Meshy API Key Not Configured")
            else:
                st.session_state.is_generating = True
                st.session_state.generation_mode = "text" # 记录模式
                st.session_state.generation_complete = False
                st.session_state.generated_stl = None
                st.session_state.generated_glb = None
                st.session_state.model_urls = {}
                st.rerun()
        
        st.markdown(textwrap.dedent("""
        <div class="cyber-card" style="margin-top: 1rem; min-height: auto;">
          <div class="corner-bracket tl"></div>
          <div class="corner-bracket tr"></div>
          <div class="corner-bracket bl"></div>
          <div class="corner-bracket br"></div>
          <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="color: #00d4ff; margin-right: 8px;">❓</span>
            <span style="font-weight: bold; font-size: 0.9rem;">HOW TO USE</span>
          </div>
          <p style="font-size: 0.8rem; color: rgba(255,255,255,0.5); line-height: 1.6;">
            1. UPLOAD CLEAR 2D IMAGE OR ENTER TEXT PROMPT<br/>
            2. CLICK GENERATE BUTTON<br/>
            3. WAIT FOR PROCESSING (~30s)<br/>
            4. PREVIEW & DOWNLOAD GLB MODEL
          </p>
        </div>
        """), unsafe_allow_html=True)
    
    with col_right:
        st.markdown('<div class="section-label preview-label">3D 预览</div>', unsafe_allow_html=True)
        
        if st.session_state.is_generating and not st.session_state.generation_complete:
            # ... (保留加载动画逻辑)
            st.markdown('<div class="loading-animation" style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center;">', unsafe_allow_html=True)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                meshy_client = MeshyAPI(MESHY_API_KEY)
                task_id = None
                task_type = "image-to-3d"
                
                # ... (保留生成逻辑) ...
                
                # ==================== Image Mode ====================
                if st.session_state.get("generation_mode") == "image":
                    status_text.markdown('<p class="loading-text" style="color: #00d4ff;">📤 UPLOADING IMAGE...</p>', unsafe_allow_html=True)
                    progress_bar.progress(5)
                    
                    uploaded_file = st.session_state.uploaded_file
                    uploaded_file.seek(0)
                    image_data = uploaded_file.read()
                    
                    status_text.markdown('<p class="loading-text" style="color: #00d4ff;">🚀 CREATING TASK...</p>', unsafe_allow_html=True)
                    progress_bar.progress(10)
                    
                    task_id = meshy_client.create_image_to_3d_task(
                        image_data=image_data,
                        file_name=uploaded_file.name,
                        ai_model="meshy-6",
                        should_texture=True,
                        topology="quad",
                        target_polycount=60000
                    )
                    task_type = "image-to-3d"
                
                # ==================== Text Mode ====================
                elif st.session_state.get("generation_mode") == "text":
                    status_text.markdown('<p class="loading-text" style="color: #00d4ff;">📝 PARSING PROMPT...</p>', unsafe_allow_html=True)
                    progress_bar.progress(5)
                    
                    prompt = st.session_state.text_prompt_input
                    
                    status_text.markdown('<p class="loading-text" style="color: #00d4ff;">🚀 CREATING TASK...</p>', unsafe_allow_html=True)
                    progress_bar.progress(10)
                    
                    task_id = meshy_client.create_text_to_3d_task(
                        prompt=prompt,
                        ai_model="meshy-6",
                        topology="quad",
                        target_polycount=60000,
                        should_remesh=True
                    )
                    task_type = "text-to-3d"
                
                if not task_id:
                    raise Exception("TASK CREATION FAILED")
                
                st.info(f"📋 TASK ID: `{task_id}`")
                
                # 3. 轮询进度
                def progress_callback(status, progress):
                    mapped_progress = 10 + int(progress * 0.85)
                    progress_bar.progress(min(mapped_progress, 95))
                    
                    if status in ['IN_PROGRESS', 'PENDING']:
                        status_text.markdown(f'<p class="loading-text" style="color: #00d4ff;">⚡ PROCESSING... ({progress}%)</p>', unsafe_allow_html=True)
                
                result = meshy_client.poll_task(task_id, task_type=task_type, progress_callback=progress_callback)
                
                # 4. 下载模型文件
                progress_bar.progress(95)
                status_text.markdown('<p class="loading-text" style="color: #00d4ff;">✨ DOWNLOADING MODEL...</p>', unsafe_allow_html=True)
                
                model_urls = meshy_client.get_model_urls(result)
                st.session_state.model_urls = model_urls
                
                if model_urls:
                    # 优先下载 STL (3D打印格式)
                    stl_url = model_urls.get("stl")
                    glb_url = model_urls.get("glb")
                    
                    if stl_url:
                        stl_data = meshy_client.download_model(stl_url)
                        st.session_state.generated_stl = stl_data
                    
                    if glb_url:
                        glb_data = meshy_client.download_model(glb_url)
                        st.session_state.generated_glb = glb_data
                    
                    progress_bar.progress(100)
                    st.session_state.generation_complete = True
                    st.session_state.is_generating = False
                    st.rerun()
                else:
                    raise Exception("NO MODEL URL FOUND")
                    
            except Exception as e:
                st.error(f"❌ ERROR: {str(e)}")
                st.session_state.is_generating = False
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.generation_complete:
            st.markdown('<div class="success-message" style="background: rgba(0, 212, 255, 0.1); border: 1px solid #00d4ff; color: #00d4ff; margin-bottom: 1rem; font-size: 1.2rem;">🎉 GENERATION COMPLETE</div>', unsafe_allow_html=True)
            
            # 3D 预览 (使用 GLB)
            if st.session_state.get('generated_glb') or st.session_state.get('model_urls', {}).get('glb'):
                
                model_url = st.session_state.get('model_urls', {}).get('glb') or ""
                model_b64 = ""
                if st.session_state.get('generated_glb'):
                    glb_bytes = st.session_state.generated_glb
                    if isinstance(glb_bytes, (bytes, bytearray)) and len(glb_bytes) <= 30 * 1024 * 1024:
                        model_b64 = base64.b64encode(glb_bytes).decode()
                
                html_code = f"""
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ margin: 0; background: transparent; }}
                    .preview-container {{
                        position: relative;
                        width: 100%;
                        height: 500px;
                        background: #0b1220;
                        border-radius: 20px;
                        border: 1px solid rgba(255, 255, 255, 0.05);
                        box-shadow: 0 0 50px rgba(0, 0, 0, 0.5) inset;
                        overflow: hidden;
                    }}
                    .bracket {{
                        position: absolute;
                        width: 40px;
                        height: 40px;
                        border: 2px solid #00d1d6;
                        pointer-events: none;
                        box-shadow: 0 0 10px #00d1d6;
                        z-index: 10;
                    }}
                    .bracket-tl {{ top: 20px; left: 20px; border-right: none; border-bottom: none; border-radius: 12px 0 0 0; }}
                    .bracket-bl {{ bottom: 20px; left: 20px; border-right: none; border-top: none; border-radius: 0 0 0 12px; }}
                    .bracket-tr {{ top: 20px; right: 20px; border-left: none; border-bottom: none; border-radius: 0 12px 0 0; }}
                    .bracket-br {{ bottom: 20px; right: 20px; border-left: none; border-top: none; border-radius: 0 0 12px 0; }}
                    model-viewer {{
                        width: 100%;
                        height: 100%;
                        background-color: transparent;
                        --poster-color: transparent;
                        --progress-bar-color: rgba(0, 209, 214, 0.8);
                        --progress-bar-height: 3px;
                    }}
                    model-viewer::part(default-progress-bar) {{
                        background-color: rgba(0, 209, 214, 0.8);
                    }}
                    .viewer-status {{
                        position: absolute;
                        left: 22px;
                        bottom: 18px;
                        z-index: 50;
                        display: none;
                        padding: 10px 12px;
                        border-radius: 12px;
                        background: rgba(0, 0, 0, 0.55);
                        border: 1px solid rgba(255, 255, 255, 0.12);
                        color: rgba(234, 240, 247, 0.92);
                        font-family: 'Inter', sans-serif;
                        font-size: 14px;
                        max-width: calc(100% - 44px);
                        backdrop-filter: blur(6px);
                    }}
                    .floating-tools {{
                        position: absolute;
                        right: 20px;
                        top: 50%;
                        transform: translateY(-50%);
                        display: flex;
                        flex-direction: column;
                        gap: 10px;
                        z-index: 100;
                    }}
                    .tool-btn {{
                        width: 50px;
                        height: 50px;
                        background: rgba(0, 0, 0, 0.5);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 10px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #00d1d6;
                        cursor: pointer;
                        backdrop-filter: blur(5px);
                        transition: all 0.2s;
                    }}
                    .tool-btn:hover {{
                        background: rgba(0, 209, 214, 0.2);
                        box-shadow: 0 0 10px rgba(0, 209, 214, 0.3);
                    }}
                    .tool-btn:active {{
                        transform: scale(0.95);
                    }}
                </style>
                <div class="preview-container">
                    <div class="bracket bracket-tl"></div>
                    <div class="bracket bracket-bl"></div>
                    <div class="bracket bracket-tr"></div>
                    <div class="bracket bracket-br"></div>
                    <div id="viewer-status" class="viewer-status"></div>
                    <model-viewer
                        id="model-viewer"
                        alt="3D Model"
                        auto-rotate
                        camera-controls
                        shadow-intensity="2"
                        shadow-softness="0.5"
                        exposure="1.2"
                        environment-image="https://modelviewer.dev/shared-assets/environments/spruit_sunrise_1k_HDR.hdr"
                        ar
                        ar-modes="webxr scene-viewer quick-look"
                        seamless-poster
                        loading="eager"
                    >
                        <div slot="progress-bar"></div>
                    </model-viewer>
                    <div class="floating-tools">
                        <div class="tool-btn" id="zoom-in" title="放大">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
                        </div>
                        <div class="tool-btn" id="zoom-out" title="缩小">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
                        </div>
                        <div class="tool-btn" id="reset-view" title="重置视角">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </div>
                    </div>
                </div>
                <script>
                    const MODEL_URL = {model_url!r};
                    const MODEL_B64 = {model_b64!r};
                    const modelViewer = document.getElementById('model-viewer');
                    const statusEl = document.getElementById('viewer-status');
                    const zoomInBtn = document.getElementById('zoom-in');
                    const zoomOutBtn = document.getElementById('zoom-out');
                    const resetBtn = document.getElementById('reset-view');
                    let currentZoom = 1;
                    const zoomStep = 0.3;
                    const minZoom = 0.2;
                    const maxZoom = 3;

                    function showStatus(message) {{
                        statusEl.textContent = message;
                        statusEl.style.display = 'block';
                    }}

                    function hideStatus() {{
                        statusEl.style.display = 'none';
                    }}

                    function b64ToBlobUrl(b64) {{
                        const binary = atob(b64);
                        const bytes = new Uint8Array(binary.length);
                        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                        const blob = new Blob([bytes], {{ type: 'model/gltf-binary' }});
                        return URL.createObjectURL(blob);
                    }}

                    function tryLoadSrc(src, timeoutMs = 20000) {{
                        return new Promise((resolve, reject) => {{
                            let done = false;
                            const onLoad = () => {{
                                if (done) return;
                                done = true;
                                cleanup();
                                resolve();
                            }};
                            const onError = () => {{
                                if (done) return;
                                done = true;
                                cleanup();
                                reject(new Error('load error'));
                            }};
                            const timer = setTimeout(() => {{
                                if (done) return;
                                done = true;
                                cleanup();
                                reject(new Error('load timeout'));
                            }}, timeoutMs);

                            function cleanup() {{
                                clearTimeout(timer);
                                modelViewer.removeEventListener('load', onLoad);
                                modelViewer.removeEventListener('error', onError);
                            }}

                            modelViewer.addEventListener('load', onLoad);
                            modelViewer.addEventListener('error', onError);
                            modelViewer.src = src;
                        }});
                    }}

                    async function ensureModelViewerLoaded() {{
                        if (customElements.get('model-viewer')) return;
                        const cdns = [
                            'https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js',
                            'https://cdn.jsdelivr.net/npm/@google/model-viewer/dist/model-viewer.min.js',
                            'https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js'
                        ];

                        showStatus('正在加载 3D 预览组件…');

                        for (const src of cdns) {{
                            try {{
                                await new Promise((resolve, reject) => {{
                                    const s = document.createElement('script');
                                    s.type = 'module';
                                    s.src = src;
                                    s.onload = () => resolve();
                                    s.onerror = () => reject(new Error('load failed'));
                                    document.head.appendChild(s);
                                }});

                                if (customElements.get('model-viewer')) return;
                            }} catch (e) {{
                            }}
                        }}

                        throw new Error('无法加载 3D 预览组件（CDN 访问失败）');
                    }}

                    async function initModel() {{
                        try {{
                            await ensureModelViewerLoaded();

                            if (MODEL_URL && MODEL_URL.length > 0) {{
                                showStatus('正在加载 3D 模型…');
                                try {{
                                    await tryLoadSrc(MODEL_URL);
                                    hideStatus();
                                    return;
                                }} catch (e) {{
                                }}
                            }}

                            if (MODEL_B64 && MODEL_B64.length > 0) {{
                                showStatus('正在加载 3D 模型（本地模式）…');
                                const blobUrl = b64ToBlobUrl(MODEL_B64);
                                await tryLoadSrc(blobUrl);
                                hideStatus();
                                return;
                            }}

                            // 尝试降级：如果模型过大且有URL，尝试通过URL加载（虽然可能跨域）
                            if (MODEL_URL && MODEL_URL.length > 0 && (!MODEL_B64 || MODEL_B64.length === 0)) {{
                                showStatus('尝试加载大模型（远程模式）…');
                                try {{
                                    await tryLoadSrc(MODEL_URL);
                                    hideStatus();
                                    return;
                                }} catch (e) {{}}
                            }}

                            showStatus('3D 预览加载失败：模型链接不可用或模型过大无法内嵌（>30MB）');
                        }} catch (e) {{
                            showStatus('3D 预览加载失败：' + (e && e.message ? e.message : String(e)));
                        }}
                    }}

                    initModel();
                    
                    zoomInBtn.addEventListener('click', () => {{
                        currentZoom = Math.min(currentZoom + zoomStep, maxZoom);
                        modelViewer.fieldOfView = Math.max(10, 45 / currentZoom);
                    }});
                    
                    zoomOutBtn.addEventListener('click', () => {{
                        currentZoom = Math.max(currentZoom - zoomStep, minZoom);
                        modelViewer.fieldOfView = Math.min(90, 45 / currentZoom);
                    }});
                    
                    resetBtn.addEventListener('click', () => {{
                        currentZoom = 1;
                        modelViewer.fieldOfView = 45;
                        modelViewer.cameraOrbit = 'auto auto auto';
                        modelViewer.cameraTarget = 'auto auto auto';
                    }});
                </script>
                """
                st.components.v1.html(html_code, height=520)
            
            # GLB 下载
            if st.session_state.get('generated_glb'):
                glb_b64 = base64.b64encode(st.session_state.generated_glb).decode()
                glb_link = f'<a href="data:model/gltf-binary;base64,{glb_b64}" download="snap3d_model.glb" style="display: flex; align-items: center; justify-content: center; background: linear-gradient(90deg, #00d4ff, #7c3aed); color: white; text-decoration: none; padding: 1.2rem; border-radius: 12px; font-weight: 700; font-family: \'JetBrains Mono\'; font-size: 1.2rem; letter-spacing: 1px; margin-top: 1rem; transition: all 0.3s ease;"><span>📥 DOWNLOAD GLB MODEL</span></a>'
                st.markdown(glb_link, unsafe_allow_html=True)
            
        else:
            # 初始等待状态 - 动态 3D 线框球体 (在预览面板内)
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    margin: 0; 
                    background: transparent; 
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    height: 100%; 
                    overflow: hidden; 
                    font-family: 'JetBrains Mono', monospace; 
                }
                
                .preview-panel {
                    position: relative;
                    width: 100%;
                    height: 520px;
                    background: #0b1220;
                    border-radius: 20px;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    box-shadow: 0 0 50px rgba(0, 0, 0, 0.5) inset;
                    overflow: hidden;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                
                .bracket {
                    position: absolute;
                    width: 40px;
                    height: 40px;
                    border: 2px solid #00d1d6;
                    pointer-events: none;
                    box-shadow: 0 0 10px #00d1d6;
                }
                .bracket-tl { top: 20px; left: 20px; border-right: none; border-bottom: none; border-radius: 12px 0 0 0; }
                .bracket-bl { bottom: 20px; left: 20px; border-right: none; border-top: none; border-radius: 0 0 0 12px; }
                .bracket-tr { top: 20px; right: 20px; border-left: none; border-bottom: none; border-radius: 0 12px 0 0; }
                .bracket-br { bottom: 20px; right: 20px; border-left: none; border-top: none; border-radius: 0 0 12px 0; }
                
                .container {
                    position: relative;
                    width: 100%;
                    height: 100%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    perspective: 1000px;
                }
                
                .sphere-wrapper {
                    position: relative;
                    width: 200px;
                    height: 200px;
                    transform-style: preserve-3d;
                    animation: global-rotate 20s linear infinite;
                }
                
                .ring {
                    position: absolute;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    border: 1px solid rgba(0, 209, 214, 0.1);
                    border-radius: 50%;
                    box-shadow: 0 0 15px rgba(0, 209, 214, 0.05);
                }
                
                .ring:nth-child(1) { transform: rotateY(0deg); border-left: 2px solid #00d1d6; border-right: 2px solid transparent; }
                .ring:nth-child(2) { transform: rotateY(60deg); border-top: 2px solid #7c3aed; border-bottom: 2px solid transparent; }
                .ring:nth-child(3) { transform: rotateY(120deg); border-left: 2px solid #00d1d6; border-right: 2px solid transparent; }
                .ring:nth-child(4) { transform: rotateX(60deg); border-top: 2px solid #7c3aed; border-bottom: 2px solid transparent; }
                .ring:nth-child(5) { transform: rotateX(120deg); border-left: 2px solid #00d1d6; border-right: 2px solid transparent; }
                .ring:nth-child(6) { transform: rotateZ(90deg); border: 1px dashed rgba(255, 255, 255, 0.1); }

                .cube {
                    position: absolute;
                    top: 50%; left: 50%;
                    width: 40px; height: 40px;
                    margin-top: -20px; margin-left: -20px;
                    transform-style: preserve-3d;
                    animation: cube-spin 6s linear infinite reverse;
                }
                
                .face {
                    position: absolute;
                    width: 40px; height: 40px;
                    background: rgba(0, 209, 214, 0.1);
                    border: 1px solid #00d1d6;
                    box-shadow: 0 0 20px rgba(0, 209, 214, 0.4);
                }
                
                .front  { transform: translateZ(20px); }
                .back   { transform: translateZ(-20px); }
                .right  { transform: rotateY(90deg) translateZ(20px); }
                .left   { transform: rotateY(-90deg) translateZ(20px); }
                .top    { transform: rotateX(90deg) translateZ(20px); }
                .bottom { transform: rotateX(-90deg) translateZ(20px); }
                
                .text-container {
                    position: absolute;
                    bottom: 60px;
                    left: 50%;
                    transform: translateX(-50%);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    z-index: 10;
                }

                .text {
                    color: #00d1d6;
                    font-size: 16px;
                    letter-spacing: 2px;
                    text-shadow: 0 0 10px #00d1d6;
                    animation: text-pulse 2s infinite ease-in-out;
                    font-weight: bold;
                }
                
                .floating-tools {
                    position: absolute;
                    right: 20px;
                    top: 50%;
                    transform: translateY(-50%);
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    z-index: 100;
                }
                .tool-btn {
                    width: 44px;
                    height: 44px;
                    background: rgba(0, 0, 0, 0.5);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #00d1d6;
                    cursor: pointer;
                    backdrop-filter: blur(5px);
                    transition: all 0.2s;
                }
                .tool-btn:hover {
                    background: rgba(0, 209, 214, 0.2);
                    box-shadow: 0 0 10px rgba(0, 209, 214, 0.3);
                }
                
                @keyframes global-rotate {
                    0% { transform: rotateY(0deg) rotateX(15deg); }
                    100% { transform: rotateY(360deg) rotateX(15deg); }
                }
                
                @keyframes cube-spin {
                    0% { transform: rotateX(0deg) rotateY(0deg); }
                    100% { transform: rotateX(360deg) rotateY(360deg); }
                }
                
                @keyframes text-pulse {
                    0%, 100% { opacity: 0.6; }
                    50% { opacity: 1; text-shadow: 0 0 20px #00d1d6; }
                }
            </style>
            </head>
            <body>
                <div class="preview-panel">
                    <div class="bracket bracket-tl"></div>
                    <div class="bracket bracket-bl"></div>
                    <div class="bracket bracket-tr"></div>
                    <div class="bracket bracket-br"></div>
                    
                    <div class="container">
                        <div class="sphere-wrapper">
                            <div class="ring"></div>
                            <div class="ring"></div>
                            <div class="ring"></div>
                            <div class="ring"></div>
                            <div class="ring"></div>
                            <div class="ring"></div>
                            
                            <div class="cube">
                                <div class="face front"></div>
                                <div class="face back"></div>
                                <div class="face right"></div>
                                <div class="face left"></div>
                                <div class="face top"></div>
                                <div class="face bottom"></div>
                            </div>
                        </div>
                        <div class="text-container">
                            <div class="text">等待生成</div>
                        </div>
                    </div>
                    
                    <div class="floating-tools">
                        <div class="tool-btn">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
                        </div>
                        <div class="tool-btn">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
                        </div>
                        <div class="tool-btn">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            st.components.v1.html(html_content, height=540)

if __name__ == "__main__":
    main()
