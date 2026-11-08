# ... imports ...                                                                   
import tiktoken  # pip install tiktoken                                             
from tenacity import retry, stop_after_attempt, wait_exponential,                   
retry_if_exception_type                                                             
from openai import RateLimitError, APIConnectionError, APIStatusError               
                                                                                    
# ... load_dotenv, console, system_content ...                                      
                                                                                    
class Client:                                                                       
    MAX_HISTORY_TOKENS = 12000  # Лимит под контекст модели (оставляем запас под    
ответ)                                                                              
    ENCODER = tiktoken.get_encoding("cl100k_base")  # Приблизительно для новых      
моделей                                                                             
                                                                                    
    def __init__(self, model: str = None, base_url: str =                           
'https://openrouter.ai/api/v1', ...):                                               
        self.model = model or os.getenv("MODEL_NAME",                               
"nvidia/nemotron-3-ultra-550b-a55b:free")                                           
        self.__client = OpenAI(base_url=base_url,                                   
api_key=os.getenv('OPENROUTER_API_KEY'), ...)                                       
        self._messages = [{'role': 'system', 'content': system_content}]            
        self._load_history() # Опционально                                          
                                                                                    
    def _count_tokens(self, messages: list) -> int:                                 
        # Грубый подсчет, для точного нужно считать по спецификации формата чата    
        return sum(len(self.ENCODER.encode(m.get('content', ''))) for m in          
messages)                                                                           
                                                                                    
    def _trim_history(self):                                                        
        # Удаляем старые пары user/assistant, пока не влезем в лимит                
        # Системный промпт (index 0) не трогаем                                     
        while self._count_tokens(self._messages) > self.MAX_HISTORY_TOKENS and      
len(self._messages) > 1:                                                            
            # Удаляем второе сообщение (первое после system), чтобы сохранить       
парность                                                                            
            self._messages.pop(1)                                                   
                                                                                    
    @retry(                                                                         
        wait=wait_exponential(multiplier=1, min=2, max=10),                         
        stop=stop_after_attempt(3),                                                 
        retry=retry_if_exception_type((RateLimitError, APIConnectionError,          
APIStatusError))                                                                    
    )                                                                               
    def _create_completion(self, messages):                                         
        return self.__client.chat.completions.create(                               
            model=self.model,                                                       
            messages=messages,                                                      
            stream=True,                                                            
            temperature=0.3, # Не дефолт                                            
        )                                                                           
                                                                                    
    def chat(self, user_text: str) -> str:                                          
        self._messages.append({'role': 'user', 'content': user_text})               
        self._trim_history()                                                        
                                                                                    
        response = self._create_completion(self._messages)                          
                                                                                    
        accumulated = []                                                            
        # Буферизация вывода                                                        
        buffer = ""                                                                 
        FLUSH_THRESHOLD = 80 # символов                                             
                                                                                    
        with Live(console=console, refresh_per_second=15,                           
vertical_overflow="visible") as live:                                               
            for chunk in response:                                                  
                delta = chunk.choices[0].delta.content                              
                if delta:                                                           
                    accumulated.append(delta)                                       
                    buffer += delta                                                 
                    if len(buffer) >= FLUSH_THRESHOLD or delta.endswith(('\n', '.   
', '! ', '? ')):                                                                    
                        live.update(Markdown("".join(accumulated)))                 
                        buffer = ""                                                 
            # Финальный флаш                                                        
            if buffer:                                                              
                live.update(Markdown("".join(accumulated)))                         
                                                                                    
        full_reply = "".join(accumulated)                                           
        self._messages.append({'role': 'assistant', 'content': full_reply})         
        self._save_history() # Опционально                                          
        return full_reply                                                           
                                                                                    
# ... main loop использует client.chat(...) ...