from ollama import chat

class Mentris_01:
    def __init__(self):
        # Inicializa o histórico de mensagens
        self.messages = [
            {'role': 'system', 'content': 'Responda em português brasileiro.'},
            {'role': 'user', 'content': 'content'},
            {'role': 'assistant', 'content': 'content'}
        ]
    
    def processa_resposta(self, user_input, callback=None):
        """Processa a resposta do modelo e retorna a resposta completa ou envia chunks via callback."""
        response_stream = chat(
            model='gemma3:4b',
            messages=self.messages + [{'role': 'user', 'content': user_input}],
            stream=True,
            options= {
                'temperature': 0.7,
            }
        )
        
        resposta_completa = ""
        for chunk in response_stream:
            content = chunk['message']['content']
            resposta_completa += content  # Concatena os pedaços da resposta
            
            # Se tiver uma função de callback, envia cada chunk para ela
            if callback:
                callback(content)
        
        # Atualiza o histórico de mensagens
        self.atualiza_messages(user_input, resposta_completa)
        
        return resposta_completa
    
    def atualiza_messages(self, user_input, resposta_assistente):
        """Atualiza o histórico de mensagens."""
        self.messages += [
            {'role': 'user', 'content': user_input},
            {'role': 'assistant', 'content': resposta_assistente}
        ]