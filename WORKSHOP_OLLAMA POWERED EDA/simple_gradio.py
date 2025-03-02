import gradio as gr
def square(number):
    return number ** 2
    
interface = gr.Interface(fn=square,inputs='number',outputs='number')

interface.launch()

