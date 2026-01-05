---
title: Echo Lusi AI Studio
emoji: 🎤
colorFrom: purple
colorTo: indigo
sdk: gradio
sdk_version: 4.12.0
app_file: app.py
pinned: false
---
import gradio as gr
def update(name):
    return f"Welcome to Gradio, {name}!"

with gr.Blocks() as demo:
    gr.Markdown("Start typing below and then click **Run** to see the output.")
    with gr.Row():
        inp = gr.Textbox(placeholder="What is your name?")
        out = gr.Textbox()
    btn = gr.Button("Run")
    btn.click(fn=update, inputs=inp, outputs=out)

demo.launch()
# Echo Lusi - AI Voice Studio
Profesjonalne klonowanie głosu dla Twoich piosenek.
