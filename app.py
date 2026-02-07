import gradio as gr
import os
import subprocess
from pydub import AudioSegment
import gc
import torch
import sys

def clean_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def process_song(suno_audio, user_voice_sample):
    try:
        if not suno_audio or not user_voice_sample:
            return None, "❌ Wybierz oba pliki audio!"

        clean_memory()
        
        # 1. Przygotowanie (Max 20s dla absolutnej pewności na tym RAMie)
        suno_path = os.path.abspath("temp_suno.wav")
        voice_path = os.path.abspath("temp_voice.wav")
        
        print("Ładowanie plików...")
        suno_audio_seg = AudioSegment.from_file(suno_audio)[:20000] # 20s
        suno_audio_seg.export(suno_path, format="wav")
        
        voice_audio_seg = AudioSegment.from_file(user_voice_sample)
        voice_audio_seg.export(voice_path, format="wav")
        
        del suno_audio_seg, voice_audio_seg
        clean_memory()

        # 2. Separacja (Demucs)
        print("Krok 1/3: Separacja wokalu...")
        # Używamy lżejszego modelu 'mdx_extra_q' jeśli dostępny, lub standardowego
        subprocess.run(["python3", "-m", "demucs", "--two-stems", "vocals", "-n", "htdemucs", suno_path, "-o", "output_sep"], check=True)
        
        base_name = os.path.splitext(os.path.basename(suno_path))[0]
        vocal_path = os.path.abspath(f"output_sep/htdemucs/{base_name}/vocals.wav")
        instrumental_path = os.path.abspath(f"output_sep/htdemucs/{base_name}/no_vocals.wav")
        
        clean_memory()

        # 3. Konwersja (RVC)
        print("Krok 2/3: Klonowanie głosu...")
        output_vocal = os.path.abspath("output_rvc_vocal.wav")
        env = os.environ.copy()
        env["PYTHONPATH"] = env.get("PYTHONPATH", "") + ":/home/ubuntu/RVC-WebUI"
        
        subprocess.run([
            "python3", "/home/ubuntu/voice_clone_project/infer_rvc.py",
            vocal_path, "user_voice", output_vocal
        ], check=True, env=env)
        
        clean_memory()

        # 4. Miksowanie
        print("Krok 3/3: Miksowanie finalne...")
        vocal = AudioSegment.from_wav(output_vocal)
        instrumental = AudioSegment.from_wav(instrumental_path)
        combined = instrumental.overlay(vocal)
        
        final_path = os.path.abspath("final_cover.mp3")
        combined.export(final_path, format="mp3")
        
        return final_path, "✅ SUKCES! Cover wygenerowany pomyślnie."
    except Exception as e:
        return None, f"❌ BŁĄD SYSTEMU: {str(e)}"

# Luksusowy Design Cyberpunk / Music Studio
custom_css = """
body { background-color: #000000 !important; font-family: 'Inter', sans-serif; }
.gradio-container { background-color: #000000 !important; border: none !important; }
.block { background-color: #0a0a0a !important; border: 1px solid #1a1a1a !important; border-radius: 20px !important; padding: 20px !important; }
h1 { color: #00f2ff !important; text-shadow: 0 0 15px #00f2ff; font-weight: 900 !important; text-align: center; }
.primary-btn { background: linear-gradient(135deg, #00f2ff, #7000ff) !important; border: none !important; color: white !important; font-weight: bold !important; border-radius: 10px !important; box-shadow: 0 0 20px rgba(112, 0, 255, 0.5); transition: 0.3s !important; }
.primary-btn:hover { transform: scale(1.02); box-shadow: 0 0 30px rgba(0, 242, 255, 0.7); }
label { color: #00f2ff !important; font-size: 14px !important; text-transform: uppercase; letter-spacing: 1px; }
.audio-player { background-color: #111 !important; border-radius: 10px !important; }
"""

with gr.Blocks(css=custom_css, title="ECHO LUSI - AI STUDIO V4") as demo:
    gr.Markdown("# ⚡ ECHO LUSI - AI VOICE STUDIO V4")
    gr.Markdown("<p style='text-align: center; color: #888;'>Profesjonalne studio klonowania głosu. Zoptymalizowane pod kątem stabilności.</p>")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🛠️ WEJŚCIE")
            suno_input = gr.Audio(label="🎵 Utwór z Suno", type="filepath", elem_classes="audio-player")
            voice_input = gr.Audio(label="🎙️ Twój Głos", type="filepath", elem_classes="audio-player")
            btn = gr.Button("🔥 GENERUJ COVER AI", variant="primary", elem_classes="primary-btn")
            
        with gr.Column(scale=1):
            gr.Markdown("### 🎧 WYNIK")
            audio_output = gr.Audio(label="Gotowy Cover", interactive=False, elem_classes="audio-player")
            status_msg = gr.Textbox(label="📡 Status Systemu", interactive=False, placeholder="Oczekiwanie na start...")

    btn.click(process_song, inputs=[suno_input, voice_input], outputs=[audio_output, status_msg])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
