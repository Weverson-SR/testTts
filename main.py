import sys
from PyQt6.QtWidgets import QApplication
from interface import ChatWindow, configurar_aparencia
from mentris_01 import Mentris_01

def main():
    """
    Função principal para executar o ChatWindow e o Mentris_01.
    """
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Para aparência consistente entre plataformas

    # Configurar aparência
    configurar_aparencia(app)

    # Inicializar a janela de chat
    window = ChatWindow()
    window.show()

    # Executar a aplicação
    sys.exit(app.exec())

if __name__ == "__main__":
    main()