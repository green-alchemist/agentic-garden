# src/inference.py
from llama_cpp import Llama
import os

MODELS_CONFIG = {
    "chatml": { 
        "load_params": {"n_ctx": 4096}, 
        "generation_params": {"temperature": 0.1} # Default creative temperature
    },
    "default": { 
        "load_params": {"n_ctx": 4096}, 
        "generation_params": {"temperature": 0.1} 
    }
}

def get_model_config(model_name: str) -> dict:
    model_name_lower = model_name.lower()
    if any(k in model_name_lower for k in ["hermes", "capybara"]):
        print("🔍 Detected ChatML model. Using ChatML config.")
        return MODELS_CONFIG["chatml"]
    else:
        print("🔍 Using default config.")
        return MODELS_CONFIG["default"]

class ModelManager:
    _instance = None
    llm = None
    model_name = None
    config = None

    def __new__(cls):
        if cls._instance is None:
            print("🧠 Initializing Model Manager...")
            cls._instance = super(ModelManager, cls).__new__(cls)
            
            cls.model_name = os.getenv("MODEL_NAME")
            if not cls.model_name:
                raise ValueError("MODEL_NAME environment variable not set.")
                
            model_path = os.path.join("/app/models", cls.model_name)
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}.")

            cls.config = get_model_config(cls.model_name)
            load_params = cls.config.get("load_params", {})
            print(f"⚙️ Applying load parameters: {load_params}")

            try:
                cls.llm = Llama(
                    model_path=model_path,
                    n_gpu_layers=-1,
                    verbose=True,
                    **load_params
                )
                print("✅ Model loaded successfully into GPU.")
            except Exception as e:
                raise RuntimeError(f"❌ Error loading model: {e}")
        return cls._instance

    def _prepare_generation_kwargs(self, **kwargs) -> dict:
        """Merges default model params with incoming API params."""
        # Start with the model's default generation parameters
        final_kwargs = self.config.get("generation_params", {}).copy()
        
        # ** THE FIX IS HERE: Update defaults with API values **
        # This ensures 'temperature': 0.1 from the API call overwrites any default.
        final_kwargs.update(kwargs)
        
        print(f"⚙️ Applying generation parameters: {final_kwargs}")
        return final_kwargs

    def generate_chat_completion(self, messages: list, **kwargs) -> str:
        """Generates a non-streaming chat completion."""
        final_kwargs = self._prepare_generation_kwargs(**kwargs)
        output = self.llm.create_chat_completion(
            messages=messages, stream=False, **final_kwargs
        )
        return output['choices'][0]['message']['content']

    def generate_chat_completion_stream(self, messages: list, **kwargs):
        """Generates a streaming chat completion."""
        final_kwargs = self._prepare_generation_kwargs(**kwargs)
        stream = self.llm.create_chat_completion(
            messages=messages, stream=True, **final_kwargs
        )
        for output in stream:
            if content := output["choices"][0]["delta"].get("content"):
                yield content

model_manager = ModelManager()