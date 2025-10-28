import tensorflow as tf
from transformers import TFAutoModelForSequenceClassification, AutoTokenizer
import numpy as np

# Load pre-trained model (downloads/converts ~500MB first time—runs on CPU)
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = TFAutoModelForSequenceClassification.from_pretrained(MODEL_NAME, from_pt=True)  # Key fix: Converts PyTorch weights to TF

def analyze_sentiment(text: str) -> str:
    """
    Analyzes text sentiment: NEGATIVE, NEUTRAL, POSITIVE.
    """
    inputs = tokenizer(text, return_tensors="tf", truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)
    predictions = tf.nn.softmax(outputs.logits, axis=-1)
    predicted_class = tf.argmax(predictions, axis=-1).numpy()[0]
    
    # Use model's config for labels (dynamic & accurate)
    label = model.config.id2label[predicted_class]
    return label.replace('LABEL_', '').upper()  # Clean to NEGATIVE/NEUTRAL/POSITIVE

# Test it standalone
if __name__ == "__main__":
    print(analyze_sentiment("I love this app!"))  # Now: POSITIVE
    print(analyze_sentiment("This is okay."))     # NEUTRAL
    print(analyze_sentiment("Your fees are too high! This sucks."))  # NEGATIVE
