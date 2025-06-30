import pyttsx3
import time

def iniciar_engine():
    engine = pyttsx3.init()
    engine.setProperty('rate', 200)      # Velocidade da fala
    engine.setProperty('volume', 1.0)    # Volume (0.0 a 1.0)

    # Seleciona a voz da Maria
    for voice in engine.getProperty('voices'):
        if "Maria" in voice.name:
            engine.setProperty('voice', voice.id)
            break
    return engine

def falar(texto, pausa=0.2, dividir=True):
    engine = iniciar_engine()

    if dividir:
        # Divide por pontuação para melhorar a fluidez
        partes = [parte.strip() for parte in texto.replace("...", ".").replace("!", ".").replace("?", ".").split(".") if parte]
    else:
        partes = [texto]

    for parte in partes:
        engine.say(parte)
        engine.runAndWait()
        time.sleep(pausa)  # Pausa entre frases
