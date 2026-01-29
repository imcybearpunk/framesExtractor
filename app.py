import streamlit as st
import yt_dlp
import cv2
import os
import shutil
import zipfile

# Título de la App Web
st.set_page_config(page_title="Extractor de Frames IA", page_icon="🎬")
st.title("🎬 Extractor de Frames para IA")
st.write("Sube videos de YouTube, extrae frames y descárgalos en ZIP.")

# --- ENTRADAS DE USUARIO ---
url = st.text_input("🔗 Link de YouTube")
col1, col2, col3 = st.columns(3)
with col1:
    fps_input = st.selectbox("FPS de Extracción", [5, 8, 12, 15, 24, 30, 60], index=3)
with col2:
    res_input = st.selectbox("Resolución (Altura)", ["512p", "720p", "1080p", "Original"], index=1)
with col3:
    sufijo = st.text_input("Sufijo (ej: _input)", value="_input")

# --- LÓGICA DE PROCESAMIENTO ---
def procesar_video():
    if not url:
        st.error("¡Pega un link primero!")
        return

    # Crear carpetas temporales
    work_dir = "temp_workspace"
    if os.path.exists(work_dir): shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    
    frames_dir = os.path.join(work_dir, "frames")
    os.makedirs(frames_dir)

    status_text = st.empty()
    progress_bar = st.progress(0)

    # 1. Descargar
    status_text.text("⬇️ Descargando video...")
    video_path = os.path.join(work_dir, "video.mp4")
    ydl_opts = {'format': 'best[ext=mp4]', 'outtmpl': video_path, 'quiet': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        st.error(f"Error descargando: {e}")
        return

    # 2. Procesar con OpenCV
    status_text.text("📸 Extrayendo frames... (esto toma tiempo)")
    cap = cv2.VideoCapture(video_path)
    fps_orig = cap.get(cv2.CAP_PROP_FPS)
    step = fps_orig / float(fps_input)
    
    # Calcular resolucion
    h_orig = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w_orig = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    target_h = h_orig
    if res_input != "Original":
        target_h = int(res_input.replace("p",""))
    target_w = int(target_h * (w_orig / h_orig))

    count = 0
    nxt = 0
    total_estimated = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / step)

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        if cap.get(cv2.CAP_PROP_POS_FRAMES) >= int(nxt):
            if target_h != h_orig:
                frame = cv2.resize(frame, (target_w, target_h))
            
            name = f"frame_{count:05d}{sufijo}.jpg"
            cv2.imwrite(os.path.join(frames_dir, name), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            
            count += 1
            nxt += step
            
            # Actualizar barra
            if total_estimated > 0:
                prog = min(count / total_estimated, 1.0)
                progress_bar.progress(prog)

    cap.release()
    progress_bar.progress(100)
    status_text.text("✅ ¡Listo! Comprimiendo ZIP...")

    # 3. Crear ZIP
    zip_path = "frames_resultado.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(frames_dir):
            for file in files:
                zipf.write(os.path.join(root, file), file)

    # 4. Botón de Descarga
    with open(zip_path, "rb") as f:
        st.download_button(
            label="📥 DESCARGAR ZIP CON FRAMES",
            data=f,
            file_name=f"frames_{fps_input}fps.zip",
            mime="application/zip"
        )
    
    # Limpieza
    shutil.rmtree(work_dir)

if st.button("🚀 COMENZAR PROCESO", type="primary"):
    procesar_video()
