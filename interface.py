from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton
)
from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSlot, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QTextCursor, QIcon
import speech_recognition as sr
from vozTTS import falar
from mentris_01 import Mentris_01



# Sinais do Worker
class WorkerSignals(QObject):
    finished = pyqtSignal(str)  # sinal para enviar a resposta completa
    chunk = pyqtSignal(str)     # sinal para enviar chunks de resposta
    error = pyqtSignal(str)     # sinal para erros
    result = pyqtSignal(str)     # sinal para resultado de voz


# Worker para processar o chat em segundo plano
class ChatWorker(QRunnable):
    def __init__(self, bot, user_input):
        super().__init__()
        self.bot = bot
        self.user_input = user_input
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            # Chama o método bloqueante que se comunica com o modelo
            # passando uma função de callback para processar cada chunk
            def chunk_callback(chunk_text):
                self.signals.chunk.emit(chunk_text)
            
            resposta_completa = self.bot.processa_resposta(
                self.user_input, 
                callback=chunk_callback
            )
            
            # Sinaliza quando terminar
            self.signals.finished.emit(resposta_completa)
        except Exception as e:
            self.signals.error.emit(str(e))


class VoiceWorker(QRunnable):
    def __init__(self, recognizer, microphone):
        super().__init__()
        self.recognizer = recognizer
        self.microphone = microphone
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            with self.microphone as src:
                self.recognizer.adjust_for_ambient_noise(src, duration=0.5)
                audio = self.recognizer.listen(src)  # bloqueia até silêncio
            text = self.recognizer.recognize_google(audio, language="pt-BR")
            self.signals.result.emit(text)
        except sr.UnknownValueError:
            self.signals.error.emit("Erro: não entendi o que falou.")
        except Exception as e:
            self.signals.error.emit(f"Erro no serviço de voz: {e}")


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mentris Chat")
        # lista para armazenar os workers
        # (não é necessário, mas pode ser útil para gerenciar os workers)
        self.workers = []
        self.entrada_por_voz = False # Flag para indicar se a entrada é por voz

        # tamnho da janela L e A
        self.setMinimumSize(700, 500)
        
        # Inicializar o bot (classe definida no mentris_01)
        self.bot = Mentris_01()
        
        # Configurar o widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Área de histórico do chat
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #3d3d3d;
            border-radius: 5px;
            padding: 8px;
        """)
        main_layout.addWidget(self.chat_history)
        
        # Layout para entrada de texto e botão
        input_layout = QHBoxLayout()
        
        # Campo de entrada de texto
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Digite sua mensagem...")
        self.input_field.setStyleSheet("""
            background-color: #333333;
            color: #ffffff;
            border: 1px solid #3d3d3d;
            border-radius: 5px;
            padding: 12px 15px;
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        # Botão de enviar
        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon("flecha.png"))
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border-radius: 5px;
                padding: 12px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        # Botão de voz
        self.voice_button = QPushButton()
        self.voice_button.setIcon(QIcon("icone_microfone.png"))
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border-radius: 5px;
                padding: 12px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
        """)
        self.voice_button.clicked.connect(self.captura_voz)
        input_layout.addWidget(self.voice_button)

        main_layout.addLayout(input_layout)

        # Aplicando estilo geral da janela
        self.setStyleSheet("""
            QMainWindow {
                background-color: #212121;
            }
        """)
        
        # Limpar o histórico inicial e mostrar mensagem de boas-vindas
        self.chat_history.clear()
        self.append_message("Mentris", "Bem-vindo! Como posso te ajudar hoje?", "#8e8e8e")
        
        # Instância do QThreadPool para gerenciar os workers
        self.threadpool = QThreadPool()


    def captura_voz(self):
        self.voice_button.setEnabled(False)

        # Mostra que está ouvindo
        self.voice_button.setText("Escutando...")

        # traz o worker iniciando os serviços de voz
        worker = VoiceWorker(sr.Recognizer(), sr.Microphone())

        # Conecta os sinais 
        worker.signals.result.connect(self.on_voice_sucesso)
        worker.signals.error.connect(self.on_voice_erro)

        # Adiciona o worker à thread pool para execução
        self.workers.append(worker)

        # Inicia o worker na thread pool
        self.threadpool.start(worker)


    def on_voice_sucesso(self, text):
        self.entrada_por_voz = True
        self.input_field.setText(text)
        self.send_button.click() # Fazer o teste retirando depois
        self.reset_voice_button()

        # Remover o worker da lista
        self.cleanup_workers()

    
    def on_voice_erro(self, msg):

        self.reset_voice_button()

        # Remover o worker da lista
        self.cleanup_workers()

    
    def reset_voice_button(self):
        self.voice_button.setEnabled(True)
        self.voice_button.setText("")

    def cleanup_workers(self):
        """Remove workers concluídos da lista."""
        self.workers = [worker for worker in self.workers if not worker.signals.finished]


    def append_message(self, sender, message, color):
        """Adiciona mensagem ao histórico do chat com formatação"""
        self.chat_history.setTextColor(QColor(color))
        self.chat_history.append(f"[{sender}]:")

        
        self.chat_history.setTextColor(QColor("#ffffff"))
        self.chat_history.append(f"{message}\n")
        
        # Rolar para a última mensagem
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_history.setTextCursor(cursor)


    @pyqtSlot()
    def send_message(self):
        """Envia a mensagem do usuário e inicia o processamento em segundo plano"""
        user_input = self.input_field.text().strip()
        if not user_input:
            return
        
        # Adiciona a mensagem do usuário na interface
        self.append_message("Você", user_input, "#4da6ff")
        self.input_field.clear()
        
        # Preparar para mostrar a resposta do Mentris
        self.resposta_atual = ""

        # Apenas adiciona o cabeçalho da mensagem do Mentris
        self.append_message("Mentris", "", "#00cc99")
        self.input_field.clear()

        # Desabilitar os controles
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        
        # Cria o worker que processa a resposta
        worker = ChatWorker(self.bot, user_input)
        worker.signals.chunk.connect(self.handle_chunk)
        worker.signals.finished.connect(self.handle_response)
        worker.signals.error.connect(self.handle_error)
        
        # Adiciona o worker à thread pool para execução
        self.threadpool.start(worker)


    @pyqtSlot(str)
    def handle_chunk(self, chunk):
        """Atualiza a interface com cada chunk da resposta do bot."""
        
        # Adiciona o chunk diretamente ao final do chat
        self.chat_history.setTextColor(QColor("#ffffff"))
        
        # Apenas insere o novo chunk no final do texto
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)
        
        # Mantém o cursor no final para mostrar o texto mais recente
        self.chat_history.setTextCursor(cursor)
        
        # Guarda o texto acumulado para atualizar o histórico depois
        self.resposta_atual += chunk


    @pyqtSlot(str)
    def handle_response(self, resposta_completa):
        """Finaliza o processamento da resposta."""
        # A resposta já foi mostrada via chunks, então só precisamos atualizar o estado
        self.bot.atualiza_messages(self.input_field.text().strip(), resposta_completa)
        
        # Reativa os controles da caixa de mensagem e do botão enviar
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()

        # falar a resposta com TTS somente se a entrada foi por voz
        if self.entrada_por_voz:
            falar(resposta_completa)
            self.entrada_por_voz = False # Desativa a flag de voz após falar


    @pyqtSlot(str)
    def handle_error(self, error_message):
        """Trata erros na execução do worker."""
        self.append_message("Sistema", f"Erro: {error_message}", "#ff6666")
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()


def configurar_aparencia(app):
    """
    Configura a aparência escura para a aplicação.
    """
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(dark_palette)

