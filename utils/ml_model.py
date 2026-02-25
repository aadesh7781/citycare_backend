# utils/ml_model.py

import torch
import torch.nn as nn
import pickle
import re
import os

# ── Model Definition ──────────────────────────────────────────────
class UrgencyModel(nn.Module):
    def __init__(self, vocab_size, embed_dim=64):
        super(UrgencyModel, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.fc1 = nn.Linear(embed_dim, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x):
        embedded = self.embedding(x)
        mask = (x != 0).float().unsqueeze(2)
        summed = (embedded * mask).sum(1)
        lengths = mask.sum(1).clamp(min=1)
        averaged = summed / lengths
        out = self.relu(self.fc1(averaged))
        return self.fc2(out)

# ── Load Model Once at Startup ────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR  = os.path.join(BASE_DIR, '..', 'models')

MODEL_PATH  = os.path.join(MODELS_DIR, 'urgency_model.pth')
VOCAB_PATH  = os.path.join(MODELS_DIR, 'vocab.pkl')
CONFIG_PATH = os.path.join(MODELS_DIR, 'model_config.pkl')

# Load vocab
with open(VOCAB_PATH, 'rb') as f:
    vocab = pickle.load(f)

# Load config
with open(CONFIG_PATH, 'rb') as f:
    config = pickle.load(f)

MAX_LEN    = config['max_len']
VOCAB_SIZE = config['vocab_size']

# Load model
model = UrgencyModel(VOCAB_SIZE)
model.load_state_dict(
    torch.load(MODEL_PATH, map_location=torch.device('cpu'))
)
model.eval()

print("✅ Urgency model loaded successfully")

# ── Helper Functions ──────────────────────────────────────────────
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def encode_text(text):
    tokens = text.split()
    encoded = [vocab.get(w, vocab["<UNK>"]) for w in tokens]
    if len(encoded) < MAX_LEN:
        encoded += [vocab["<PAD>"]] * (MAX_LEN - len(encoded))
    else:
        encoded = encoded[:MAX_LEN]
    return encoded

# ── Main Predict Function ─────────────────────────────────────────
def predict_score(text):
    cleaned  = clean_text(text)
    encoded  = encode_text(cleaned)
    tensor   = torch.tensor([encoded])

    with torch.no_grad():
        output = model(tensor)
        score  = output.item()

    return max(0, min(100, round(score)))