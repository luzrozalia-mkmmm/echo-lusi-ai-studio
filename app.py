import gradio as gr
import os
import subprocess
from pydub import AudioSegment
import gc
import torch

def process_song(suno_audio, user_voice_sample):
    try:
        if not suno_audio or not user_voice_sample:
            return None, "❌ Proszę przesłać oba pliki."

        # Czyścimy pamięć przed startem
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # 1. Przygotowanie plików (max 30s dla gwarancji stabilności)
        suno_path = os.path.abspath("temp_suno.wav")
        voice_path = os.path.abspath("temp_voice.wav")
        
        suno_audio_seg = AudioSegment.from_file(suno_audio)[:30000] # Tylko 30s
        suno_audio_seg.export(suno_path, format="wav")
        
        voice_audio_seg = AudioSegment.from_file(user_voice_sample)
        voice_audio_seg.export(voice_path, format="wav")

        # 2. Separacja (Demucs) - Uruchamiamy w osobnym procesie i czekamy
        print("Krok 1: Separacja wokalu...")
        subprocess.run(["python3", "-m", "demucs", "--two-stems", "vocals", suno_path, "-o", "output_sep"], check=True)
        
        base_name = os.path.splitext(os.path.basename(suno_path))[0]
        vocal_path = os.path.abspath(f"output_sep/htdemucs/{base_name}/vocals.wav")
        instrumental_path = os.path.abspath(f"output_sep/htdemucs/{base_name}/no_vocals.wav")

        # Czyścimy RAM po Demucs
        gc.collect()

        # 3. Konwersja (RVC)
        print("Krok 2: Klonowanie głosu...")
        output_vocal = os.path.abspath("output_rvc_vocal.wav")
        env = os.environ.copy()
        env["PYTHONPATH"] = env.get("PYTHONPATH", "") + ":/home/ubuntu/RVC-WebUI"
        
        subprocess.run([
            "python3", "/home/ubuntu/voice_clone_project/infer_rvc.py",
            vocal_path, "user_voice", output_vocal
        ], check=True, env=env)

        # 4. Miksowanie
        print("Krok 3: Miksowanie...")
        vocal = AudioSegment.from_wav(output_vocal)
        instrumental = AudioSegment.from_wav(instrumental_path)
        combined = instrumental.overlay(vocal)
        
        final_path = os.path.abspath("final_cover.mp3")
        combined.export(final_path, format="mp3")
        
        return final_path, "✅ Gotowe! Wygenerowano 30s covera."
    except Exception as e:
        return None, f"❌ Błąd: {str(e)}"

# Ręczny CSS dla prawdziwego efektu Premium Dark Mode
custom_css = """
body { background-color: #050505 !important; }
.gradio-container { background-color: #050505 !important; border: none !important; }
h1 { color: #a855f7 !important; text-shadow: 0 0 10px #a855f7; }
.primary-btn { background: linear-gradient(45deg, #6366f1, #a855f7) !important; border: none !important; box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4); }
.primary-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(168, 85, 247, 0.6); }
.block { background-color: #111111 !important; border: 1px solid #222 !important; border-radius: 15px !important; }
label { color: #94a3b8 !important; font-weight: bold !important; }
"""

with gr.Blocks(css=custom_css, title="Echo Lusi AI Studio") as demo:
    gr.Markdown("# ⚡ ECHO LUSI - AI VOICE STUDIO")
    gr.Markdown("### Twórz profesjonalne covery AI w mgnieniu oka.")
    
    with gr.Row():
        with gr.Column():
            suno_input = gr.Audio(label="🎵 Piosenka z Suno", type="filepath")
            voice_input = gr.Audio(label="🎙️ Twój Głos", type="filepath")
            btn = gr.Button("🔥 GENERUJ COVER AI", variant="primary", elem_classes="primary-btn")
            
        with gr.Column():
            audio_output = gr.Audio(label="🎧 Wynik Końcowy", interactive=False)
            status_msg = gr.Textbox(label="📡 Status Systemu", interactive=False)

    btn.click(process_song, inputs=[suno_input, voice_input], outputs=[audio_output, status_msg])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
