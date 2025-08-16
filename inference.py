# inference.py (Fully Dynamic Version)
from llama_cpp import Llama
import os

# --- 1. Comprehensive Model Configuration Dictionary ---
# This is now the complete profile for each model family.
MODELS_CONFIG = {
    "llama3": {
        "load_params": {
            "n_ctx": 8192,
            "n_batch": 512
        },
        "generation_params": {
            "temperature": 0.7,
            "top_p": 0.95
        },
        "template": "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>",
        "stop_tokens": ["<|eot_id|>", "<|end_of_text|>"]
    },
    "chatml": {
        "load_params": {
            "n_ctx": 4096,
            "n_batch": 512
        },
        "generation_params": {
            "temperature": 0.8,
            "top_p": 0.95
        },
        "template": "<|im_start|>system\nYou are a helpful AI assistant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant",
        "stop_tokens": ["<|im_end|>"]
    },
    "phi-2": {
        "load_params": {
            "n_ctx": 2048,
            "n_batch": 256
        },
        "generation_params": {
            "temperature": 0.6,
            "top_p": 0.9
        },
        "template": "Instruct: {prompt}\nOutput:",
        "stop_tokens": ["\n", "<|endoftext|>"]
    }
}

def get_model_config(model_name: str) -> dict:
    """Intelligently selects the model configuration based on the filename."""
    model_name_lower = model_name.lower()
    if "hermes" in model_name_lower:
        print("🔍 Detected Hermes model. Using ChatML config.")
        return MODELS_CONFIG["chatml"]
    elif "phi-2" in model_name_lower:
        print("🔍 Detected Phi-2 model. Using Phi-2 config.")
        return MODELS_CONFIG["phi-2"]
    else:
        print("🔍 Detected Llama model. Using Llama 3 config.")
        return MODELS_CONFIG["llama3"]

class ModelManager:
    _instance = None
    llm = None
    model_config = None

    def __new__(cls):
        if cls._instance is None:
            print("🧠 Initializing Model Manager...")
            cls._instance = super(ModelManager, cls).__new__(cls)
            
            model_name = os.getenv("MODEL_NAME", "Meta-Llama-3-8B-Instruct-Q4_K_M.gguf")
            model_path = os.path.join("/app/models", model_name)

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}.")

            cls.model_config = get_model_config(model_name)
            load_params = cls.model_config.get("load_params", {})

            print(f"🐏 Loading model from: {model_path}")
            print(f"⚙️ Applying load parameters: {load_params}")
            
            try:
                cls.llm = Llama(
                    model_path=model_path,
                    n_gpu_layers=-1,
                    verbose=True,
                    **load_params  # Unpack dynamic load parameters here
                )
                print("✅ Model loaded successfully into GPU.")
            except Exception as e:
                print(f"❌ Error loading model: {e}")
                raise
        return cls._instance
    
    def generate_chat_completion_stream(self, messages: list, **kwargs):
        """Generates a streaming chat completion from a list of messages."""
        if self.llm is None:
            raise RuntimeError("Model is not loaded.")
        
        # Add stream=True to the call
        stream = self.llm.create_chat_completion(
            messages=messages,
            stream=True,
            **kwargs
        )

        for output in stream:
            # Yield the content of each chunk
            if "content" in output["choices"][0]["delta"]:
                yield output["choices"][0]["delta"]["content"]


model_manager = ModelManager()