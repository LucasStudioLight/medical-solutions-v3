import streamlit as st
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import io
import time
import threading
import queue

class AudioVisualizer:
    def __init__(self):
        # Configurações de áudio
        self.CHUNK = 1024  # Tamanho do buffer de áudio
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 44100  # Taxa de amostragem
        self.UPDATE_INTERVAL = 0.1  # Intervalo de atualização em segundos
        
        # Inicialização do PyAudio
        self.p = pyaudio.PyAudio()
        
        # Fila para comunicação entre threads
        self.q = queue.Queue()
        
        # Flag para controle da gravação
        self.is_recording = False
        
        # Configuração do plot
        self.fig, self.ax = plt.subplots(figsize=(10, 3))
        self.ax.set_facecolor('#0E1117')
        self.fig.patch.set_facecolor('#0E1117')
        
        # Configuração dos eixos
        self.ax.set_xlim(0, self.CHUNK)
        self.ax.set_ylim(-1, 1)
        self.ax.set_title('Visualizador de Áudio', color='white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.grid(True, alpha=0.3)
        
        # Linha do plot
        self.line, = self.ax.plot([], [], lw=2, color='#00BFFF')
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback chamado quando novos dados de áudio estão disponíveis"""
        try:
            # Converte os bytes em array numpy
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Normaliza os dados
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val
            
            # Coloca os dados na fila
            self.q.put(audio_data)
            
            return (in_data, pyaudio.paContinue)
        except Exception as e:
            print(f"Erro no callback de áudio: {str(e)}")
            return (in_data, pyaudio.paComplete)
    
    def get_audio_plot(self):
        """Gera uma imagem do plot atual"""
        try:
            # Pega os dados mais recentes da fila
            try:
                data = self.q.get_nowait()
                self.line.set_data(range(len(data)), data)
            except queue.Empty:
                pass
            
            # Salva o plot em um buffer
            buf = io.BytesIO()
            self.fig.savefig(buf, format='png', 
                           facecolor=self.fig.get_facecolor(), 
                           edgecolor='none',
                           bbox_inches='tight',
                           pad_inches=0.1)
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Erro ao gerar plot: {str(e)}")
            return None
    
    def start_recording(self):
        """Inicia a gravação de áudio"""
        if self.is_recording:
            return
            
        try:
            # Abre o stream de áudio
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                stream_callback=self.audio_callback
            )
            
            # Inicia o stream
            self.stream.start_stream()
            self.is_recording = True
            
        except Exception as e:
            print(f"Erro ao iniciar gravação: {str(e)}")
            self.stop_recording()
    
    def stop_recording(self):
        """Para a gravação e limpa os recursos"""
        if not self.is_recording:
            return
            
        try:
            if hasattr(self, 'stream'):
                self.stream.stop_stream()
                self.stream.close()
            
            self.is_recording = False
            
        except Exception as e:
            print(f"Erro ao parar gravação: {str(e)}")
        
        finally:
            try:
                self.p.terminate()
            except:
                pass

def main():
    st.title("Visualizador de Áudio em Tempo Real")
    
    # Inicializa o visualizador
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = AudioVisualizer()
    
    # Botões de controle
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button('Iniciar Gravação', disabled=st.session_state.visualizer.is_recording):
            st.session_state.visualizer.start_recording()
    
    with col2:
        if st.button('Parar Gravação', disabled=not st.session_state.visualizer.is_recording):
            st.session_state.visualizer.stop_recording()
    
    # Container para o visualizador
    plot_container = st.empty()
    
    # Loop de atualização
    while st.session_state.visualizer.is_recording:
        # Atualiza o plot
        audio_plot = st.session_state.visualizer.get_audio_plot()
        if audio_plot:
            plot_container.image(audio_plot)
        
        # Pequena pausa para não sobrecarregar
        time.sleep(0.1)

if __name__ == "__main__":
    main()
