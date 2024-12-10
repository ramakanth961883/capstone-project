import os
import boto3
from flask import Flask, request, jsonify, render_template
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import tensorflow as tf
import pickle
import tempfile
import tweepy

app = Flask(__name__)

# S3 Configuration
S3_BUCKET_NAME = "salstmbert"
S3_REGION = "us-east-2"
s3_client = boto3.client("s3", region_name=S3_REGION)

def download_file_from_s3(s3_path, local_path):
    """Download a file from S3 to a local path."""
    s3_client.download_file(S3_BUCKET_NAME, s3_path, local_path)

# Temporary directory for downloading files
temp_dir = tempfile.TemporaryDirectory()

# Paths to temporary storage
transformer_model_dir = os.path.join(temp_dir.name, "transformers")
lstm_model_dir = os.path.join(temp_dir.name, "lstm")

os.makedirs(transformer_model_dir, exist_ok=True)
os.makedirs(lstm_model_dir, exist_ok=True)

# Download transformer model files from S3
download_file_from_s3("transformers/config.json", os.path.join(transformer_model_dir, "config.json"))
download_file_from_s3("transformers/model.safetensors", os.path.join(transformer_model_dir, "model.safetensors"))
download_file_from_s3("transformers/vocab.txt", os.path.join(transformer_model_dir, "vocab.txt"))
download_file_from_s3("transformers/tokenizer_config.json", os.path.join(transformer_model_dir, "tokenizer_config.json"))

# Load the transformer model and tokenizer
transformer_tokenizer = AutoTokenizer.from_pretrained(transformer_model_dir)
transformer_model = AutoModelForSequenceClassification.from_pretrained(transformer_model_dir)
transformer_analyzer = pipeline("sentiment-analysis", model=transformer_model, tokenizer=transformer_tokenizer)

# Download LSTM model files from S3
download_file_from_s3("lstm/lstm_model.h5", os.path.join(lstm_model_dir, "lstm_model.h5"))
download_file_from_s3("lstm/tokenizer.pkl", os.path.join(lstm_model_dir, "tokenizer.pkl"))

# Load the LSTM model and tokenizer
lstm_model = tf.keras.models.load_model(os.path.join(lstm_model_dir, "lstm_model.h5"))
with open(os.path.join(lstm_model_dir, "tokenizer.pkl"), "rb") as f:
    lstm_tokenizer = pickle.load(f)

# Twitter API credentials
# BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAB%2FQxQEAAAAAw6%2F%2BC3UeQl3El%2BcVZMmFJbRp%2BoA%3Dpdpi8L6UeQGww1BMfg5a0mxGVdA78I2ESHeiPq56EFs4DexSGv"

BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAAKjkxQEAAAAAgzQqq8pdZy%2Be22AjtGt38vXmf7k%3Do5OfTS8gbkpHpVwtAo6QGaMDNhF89jxLipN0KbSm5Q2p5tf9p2'
client = tweepy.Client(bearer_token=BEARER_TOKEN)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_tweets():
    try:
        query = request.form.get("query")
        num_tweets = int(request.form.get("num_tweets", 10))

        # Fetch tweets using Tweepy
        response = client.search_recent_tweets(
            query=query,
            max_results=min(num_tweets, 100),
            tweet_fields=["created_at", "text"]
        )

        if not response.data:
            return jsonify({"error": "No tweets found for the given query."})

        # Prepare tweets data
        tweets = [{"text": tweet.text, "created_at": tweet.created_at} for tweet in response.data]

        # Perform sentiment analysis using transformer model
        for tweet in tweets:
            transformer_sentiment = transformer_analyzer(tweet["text"])[0]
            tweet["transformer_sentiment"] = transformer_sentiment["label"]
            tweet["transformer_score"] = transformer_sentiment["score"]

            # Perform sentiment analysis using LSTM model
            tokenized_text = lstm_tokenizer.texts_to_sequences([tweet["text"]])
            padded_sequence = tf.keras.preprocessing.sequence.pad_sequences(tokenized_text, maxlen=50)
            lstm_prediction = lstm_model.predict(padded_sequence)[0]
            tweet["lstm_sentiment"] = "POSITIVE" if lstm_prediction > 0.5 else "NEGATIVE"
            tweet["lstm_score"] = float(lstm_prediction)

        return jsonify({"tweets": tweets})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
