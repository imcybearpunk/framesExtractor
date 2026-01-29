{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import yt_dlp\
import cv2\
import os\
import shutil\
import zipfile\
\
# T\'edtulo de la App Web\
st.set_page_config(page_title="Extractor de Frames IA", page_icon="\uc0\u55356 \u57260 ")\
st.title("\uc0\u55356 \u57260  Extractor de Frames para IA")\
st.write("Sube videos de YouTube, extrae frames y desc\'e1rgalos en ZIP.")\
\
# --- ENTRADAS DE USUARIO ---\
url = st.text_input("\uc0\u55357 \u56599  Link de YouTube")\
col1, col2, col3 = st.columns(3)\
with col1:\
    fps_input = st.selectbox("FPS de Extracci\'f3n", [5, 8, 12, 15, 24, 30, 60], index=3)\
with col2:\
    res_input = st.selectbox("Resoluci\'f3n (Altura)", ["512p", "720p", "1080p", "Original"], index=1)\
with col3:\
    sufijo = st.text_input("Sufijo (ej: _input)", value="_input")\
\
# --- L\'d3GICA DE PROCESAMIENTO ---\
def procesar_video():\
    if not url:\
        st.error("\'a1Pega un link primero!")\
        return\
\
    # Crear carpetas temporales\
    work_dir = "temp_workspace"\
    if os.path.exists(work_dir): shutil.rmtree(work_dir)\
    os.makedirs(work_dir)\
    \
    frames_dir = os.path.join(work_dir, "frames")\
    os.makedirs(frames_dir)\
\
    status_text = st.empty()\
    progress_bar = st.progress(0)\
\
    # 1. Descargar\
    status_text.text("\uc0\u11015 \u65039  Descargando video...")\
    video_path = os.path.join(work_dir, "video.mp4")\
    ydl_opts = \{'format': 'best[ext=mp4]', 'outtmpl': video_path, 'quiet': True\}\
    \
    try:\
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:\
            ydl.download([url])\
    except Exception as e:\
        st.error(f"Error descargando: \{e\}")\
        return\
\
    # 2. Procesar con OpenCV\
    status_text.text("\uc0\u55357 \u56568  Extrayendo frames... (esto toma tiempo)")\
    cap = cv2.VideoCapture(video_path)\
    fps_orig = cap.get(cv2.CAP_PROP_FPS)\
    step = fps_orig / fps_input\
    \
    # Calcular resolucion\
    h_orig = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))\
    w_orig = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))\
    target_h = h_orig\
    if res_input != "Original":\
        target_h = int(res_input.replace("p",""))\
    target_w = int(target_h * (w_orig / h_orig))\
\
    count = 0\
    nxt = 0\
    total_estimated = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / step)\
\
    while True:\
        ret, frame = cap.read()\
        if not ret: break\
        \
        if cap.get(cv2.CAP_PROP_POS_FRAMES) >= int(nxt):\
            if target_h != h_orig:\
                frame = cv2.resize(frame, (target_w, target_h))\
            \
            name = f"frame_\{count:05d\}\{sufijo\}.jpg"\
            cv2.imwrite(os.path.join(frames_dir, name), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])\
            \
            count += 1\
            nxt += step\
            \
            # Actualizar barra (con cuidado para no alentar)\
            if count % 10 == 0:\
                prog = min(count / total_estimated, 1.0)\
                progress_bar.progress(prog)\
\
    cap.release()\
    progress_bar.progress(100)\
    status_text.text("\uc0\u9989  \'a1Listo! Comprimiendo ZIP...")\
\
    # 3. Crear ZIP para descargar\
    zip_path = "frames_resultado.zip"\
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:\
        for root, dirs, files in os.walk(frames_dir):\
            for file in files:\
                zipf.write(os.path.join(root, file), file)\
\
    # 4. Bot\'f3n de Descarga\
    with open(zip_path, "rb") as f:\
        st.download_button(\
            label="\uc0\u55357 \u56549  DESCARGAR ZIP CON FRAMES",\
            data=f,\
            file_name=f"frames_\{fps_input\}fps.zip",\
            mime="application/zip"\
        )\
    \
    # Limpieza\
    shutil.rmtree(work_dir)\
\
# Bot\'f3n Principal\
if st.button("\uc0\u55357 \u56960  COMENZAR PROCESO", type="primary"):\
    procesar_video()}