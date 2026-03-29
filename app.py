#!/usr/bin/env python3
"""
Voice Clone Singer - HuggingFace Spaces Version
Simple Gradio interface for voice conversion
"""

import gradio as gr
import os
import tempfile
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import librosa

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

def process_audio(voice_sample, song_file):
    """
    Process voice and song for conversion
    """
    try:
        # Load voice sample
        if voice_sample is None:
            return None, "❌ Błąd: Brak nagrania głosu"
        
        # Load song
        if song_file is None:
            return None, "❌ Błąd: Brak pliku piosenki"
        
        # Simple processing - just return the song for now
        # In production, this would use UVR, RVC, and FFmpeg
        
        return song_file, "✅ Przetwarzanie zakończone!\n\nW pełnej wersji tutaj byłaby konwersja głosu."
        
    except Exception as e:
        return None, f"❌ Błąd: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Voice Clone Singer") as demo:
    gr.Markdown("# 🎤 Voice Clone Singer")
    gr.Markdown("Klonuj swój głos i podmieniaj wokal w piosenkach")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 1️⃣ Nagraj swój głos")
            voice_input = gr.Audio(
                label="Nagranie głosu",
                type="filepath",
                sources=["microphone", "upload"]
            )
            
        with gr.Column():
            gr.Markdown("### 2️⃣ Wgraj piosenkę")
            song_input = gr.Audio(
                label="Plik piosenki (MP3, WAV)",
                type="filepath",
                sources=["upload"]
            )
    
    gr.Markdown("### 3️⃣ Przetwórz")
    process_btn = gr.Button("🚀 Przetwórz", variant="primary", size="lg")
    
    with gr.Row():
        with gr.Column():
            output_audio = gr.Audio(label="Wynik", type="filepath")
        with gr.Column():
            status_text = gr.Textbox(label="Status", interactive=False)
    
    # Connect button
    process_btn.click(
        fn=process_audio,
        inputs=[voice_input, song_input],
        outputs=[output_audio, status_text]
    )
    
    gr.Markdown("""
    ---
    ### Jak to działa?
    1. **Nagraj głos** - Nagranie będzie klonowane
    2. **Wgraj piosenkę** - Będzie rozdzielona na wokal i instrumentał
    3. **Przetwórz** - Wokal zostanie zastąpiony Twoim głosem
    4. **Pobierz** - Pobierz piosenkę z Twoim głosem
    
    ⚠️ **Uwaga**: Pierwsza konwersja może potrwać 2-5 minut
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
