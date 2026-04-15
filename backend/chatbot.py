"""
Career Guidance Chatbot - NLP Engine
Approach: Rule-based (pattern matching) + ML-based (TF-IDF + Logistic Regression)
"""

import json
import random
import re
import os
import pickle
import numpy as np

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

# ─── NLTK downloads (safe to call multiple times) ────────────────────────────
for pkg in ["punkt", "punkt_tab", "stopwords", "wordnet"]:
    nltk.download(pkg, quiet=True)

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH = os.path.join(BASE_DIR, "intents.json")
MODEL_PATH   = os.path.join(BASE_DIR, "model.pkl")


class CareerChatbot:
    def __init__(self):
        self.lemmatizer    = WordNetLemmatizer()
        self.stop_words    = set(stopwords.words("english")) - {
            "what", "how", "which", "where", "who", "when", "why",
            "not", "no", "want", "need", "can", "should"
        }
        self.intents       = self._load_intents()
        self.pipeline      = None
        self.label_encoder = LabelEncoder()
        self.responses     = {}

        self._build_response_map()
        self._train_or_load()

    def _load_intents(self):
        with open(INTENTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)["intents"]

    def _build_response_map(self):
        for intent in self.intents:
            self.responses[intent["tag"]] = intent["responses"]

    def preprocess(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
        tokens = word_tokenize(text)
        tokens = [
            self.lemmatizer.lemmatize(t)
            for t in tokens
            if t not in self.stop_words and len(t) > 1
        ]
        return " ".join(tokens)

    def _prepare_training_data(self):
        X, y = [], []
        for intent in self.intents:
            for pattern in intent["patterns"]:
                X.append(self.preprocess(pattern))
                y.append(intent["tag"])
        return X, y

    def _train_or_load(self):
        if os.path.exists(MODEL_PATH):
            self._load_model()
        else:
            self.train()

    def train(self):
        X, y = self._prepare_training_data()
        y_enc = self.label_encoder.fit_transform(y)

        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True
            )),
            ("clf", LogisticRegression(
                max_iter=1000,
                C=10,
                solver="lbfgs",
            )),
        ])
        self.pipeline.fit(X, y_enc)
        self._save_model()
        print("✅ Model trained and saved.")

    def _save_model(self):
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({"pipeline": self.pipeline, "encoder": self.label_encoder}, f)

    def _load_model(self):
        with open(MODEL_PATH, "rb") as f:
            data = pickle.load(f)
        self.pipeline      = data["pipeline"]
        self.label_encoder = data["encoder"]
        print("✅ Model loaded from disk.")

    def _rule_based(self, text: str):
        lower = text.lower()
        
        # Enhanced rules with more variations including "from zero", "scratch", etc.
        rules = [
            # Greetings
            (["hello", "hi ", "hey", "good morning", "good evening", "hii", "hiii"], "greeting"),
            
            # Goodbyes
            (["bye", "goodbye", "see you", "take care"], "goodbye"),
            
            # Thanks
            (["thank", "thanks", "thx"], "thanks"),
            
            # Confused / Lost / Starting from zero (ENHANCED)
            (["confused", "don't know", "no idea", "lost", "can't decide"], "confused"),
            (["start from zero", "from scratch", "from the beginning", "starting fresh"], "confused"),
            (["i know nothing", "zero knowledge", "blank slate", "complete beginner"], "confused"),
            (["i have zero experience", "never worked", "no work experience"], "confused"),
            (["where do i start", "how do i start", "where to begin"], "confused"),
            (["don't understand anything", "everything is new"], "confused"),
            
            # Starting point - career options
            (["starting point", "first step", "how to begin career"], "career_options"),
            (["new to this", "just starting", "entry level"], "career_options"),
            
            # Software
            (["software", "coding", "programmer", "developer", "it job"], "software_engineering"),
            (["learn to code", "start coding", "programming from"], "software_engineering"),
            (["computer science", "btech cse", "computer engineering"], "software_engineering"),
            
            # Data Science
            (["data science", "machine learning", "ai ", "artificial intelligence"], "data_science"),
            (["data analyst", "work with data", "big data"], "data_science"),
            
            # Medicine
            (["doctor", "mbbs", "medicine", "medical", "physician"], "medicine"),
            (["become a doctor", "medical field"], "medicine"),
            
            # Business
            (["mba", "management", "business", "marketing", "finance career"], "business_management"),
            (["entrepreneur", "startup", "own business"], "business_management"),
            
            # Design
            (["design", "graphic", "ui ux", "creative", "animation"], "design"),
            (["fashion design", "interior design"], "design"),
            
            # Government
            (["government", "upsc", "ias", "ips", "ssc", "bank job", "sarkari"], "government_jobs"),
            (["public sector", "govt job", "civil services"], "government_jobs"),
            
            # Salary
            (["salary", "earn", "pay", "income", "wages", "money", "package"], "salary"),
            (["how much", "stipend", "ctc", "compensation"], "salary"),
            
            # Higher studies
            (["masters", "ms ", "m.tech", "phd", "gate", "gre", "higher studies"], "higher_studies"),
            (["post graduation", "pg", "advanced degree"], "higher_studies"),
            
            # Interviews
            (["interview", "resume", "placement", "internship"], "aptitude_test"),
            (["cv", "job application", "hr round"], "aptitude_test"),
            
            # Skills
            (["skill", "what to learn", "in demand", "tech skills"], "skills_needed"),
            (["upskill", "improve skills", "learn new"], "skills_needed"),
            
            # Career options general
            (["career option", "career path", "what career", "which career"], "career_options"),
            (["job options", "work options", "professional career"], "career_options"),
            
            # Engineering
            (["engineering", "b.tech", "be ", "mechanical", "civil", "electrical"], "engineering"),
            (["engineer", "engineering branch"], "engineering"),
        ]
        
        for keywords, tag in rules:
            if any(kw in lower for kw in keywords):
                return tag, 0.95
        return None, 0.0

    def predict_intent(self, text: str):
        tag, conf = self._rule_based(text)
        if tag:
            return tag, conf
        processed = self.preprocess(text)
        proba     = self.pipeline.predict_proba([processed])[0]
        best_idx  = int(np.argmax(proba))
        best_conf = float(proba[best_idx])
        tag       = self.label_encoder.inverse_transform([best_idx])[0]
        return tag, best_conf

    def get_response(self, user_message: str) -> dict:
        if not user_message.strip():
            return {
                "response": "Please type a message so I can help you!",
                "intent": "unknown",
                "confidence": 0.0
            }
        tag, confidence = self.predict_intent(user_message)
        if confidence < 0.30:
            response = (
                "I'm not sure I understood that completely. Could you rephrase? "
                "You can ask me about career options, salary, required skills, "
                "higher studies, or specific fields like IT, Medicine, or Engineering."
            )
            tag = "unknown"
        else:
            response = random.choice(self.responses.get(tag, [
                "I don't have specific information on that yet. "
                "Try asking about a specific career field!"
            ]))
        return {
            "response":   response,
            "intent":     tag,
            "confidence": round(confidence, 2)
        }


if __name__ == "__main__":
    bot = CareerChatbot()
    print("\n🎓 Career Guidance Chatbot (type 'quit' to exit)\n")
    while True:
        msg = input("You: ").strip()
        if msg.lower() in ("quit", "exit", "bye"):
            print("Bot: Goodbye! Best of luck!")
            break
        result = bot.get_response(msg)
        print(f"Bot [{result['intent']} | {result['confidence']}]: {result['response']}\n")
