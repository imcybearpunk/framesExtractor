import streamlit as st
import yt_dlp
import cv2
import os
import shutil
import zipfile

# Título y Configuración
st.set_page_config(page_title="Extractor IA Pro", page_icon="🎬")
st.title("🎬 Extractor de Frames IA (Versión Cloud)")
st.warning("⚠️ Nota: YouTube bloquea frecuentemente servidores en la nube. Si este método falla con 'Error 403', usa tu versión de Escritorio (Mac) que es infalible.")

# --- ENTRADAS DE USUARIO ---
url = st.text_input("🔗 Link de YouTube")

col1, col2, col3 = st.columns(3)
with col1:
    # AHORA ES UN CAMPO NUMÉRICO LIBRE
    fps_input = st.number_input("FPS de Extracción", min_value=0.1, max_value=60.0, value=15.0, step=1.0, format="%.2f")
with col2:
    res_input = st.selectbox("Resolución (Altura)", ["512p", "720p", "1080p", "Original"], index=1)
with col3:
    sufijo = st.text_input("Sufijo (ej: _input)", value="_input")

# --- LÓGICA ---
def procesar_video():
    if not url:
        st.error("¡Pega un link primero!")
        return

    # Limpiar y crear temporales
    work_dir = "temp_workspace"
    if os.path.exists(work_dir): shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    
    frames_dir = os.path.join(work_dir, "frames")
    os.makedirs(frames_dir)

    status_text = st.empty()
    progress_bar = st.progress(0)

    # 1. INTENTO DE DESCARGA ANTI-BLOQUEO
    status_text.text("⬇️ Intentando descargar (evitando bloqueo 403)...")
    video_path = os.path.join(work_dir, "video.mp4")
    
    # Opciones avanzadas para parecer un navegador real
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': video_path,
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'referer': 'https://www.youtube.com/',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        st.error(f"❌ YouTube bloqueó la descarga: {e}")
        st.info("💡 Solución: Este error pasa porque YouTube sabe que esto es un servidor. Por favor usa la App de Escritorio que creamos en tu Mac, esa usa tu IP de casa y NO fallará.")
        shutil.rmtree(work_dir) # Limpieza
        return

    # 2. PROCESAR
    status_text.text(f"📸 Extrayendo a {fps_input} FPS... (Paciencia)")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        st.error("Error al abrir el video descargado.")
        return

    fps_orig = cap.get(cv2.CAP_PROP_FPS)
    step = fps_orig / fps_input
    
    # Resolución
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
            
            if total_estimated > 0:
                prog = min(count / total_estimated, 1.0)
                progress_bar.progress(prog)

    cap.release()
    progress_bar.progress(100)
    status_text.text("✅ ¡Listo! Creando ZIP...")

    # 3. ZIP Y DESCARGA
    zip_path = "frames_resultado.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(frames_dir):
            for file in files:
                zipf.write(os.path.join(root, file), file)

    with open(zip_path, "rb") as f:
        st.download_button(
            label=f"📥 BAJAR FRAMES ({count} imgs)",
            data=f,
            file_name=f"frames_{fps_input}fps.zip",
            mime="application/zip"
        )
    
    # Limpieza final
    shutil.rmtree(work_dir)

if st.button("🚀 COMENZAR PROCESO", type="primary"):
    procesar_video()
