"""
train.py — Run this once to train and save the NLP model.
Usage:  python train.py
"""

from chatbot import CareerChatbot
import os

if __name__ == "__main__":
    print("=" * 50)
    print("  Career Guidance Chatbot — Model Trainer")
    print("=" * 50)

    # Remove old model if exists so we retrain fresh
    model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
    if os.path.exists(model_path):
        os.remove(model_path)
        print("🗑️  Old model removed.")

    print("⏳ Training model...")
    bot = CareerChatbot()

    print("\n✅ Training complete! Model saved as model.pkl")
    print("\n🧪 Quick test:")

    tests = [
        "Hello!",
        "I want to become a software engineer",
        "What is the salary for a data scientist?",
        "I am confused about my career",
        "Tell me about government jobs",
        "Should I do masters or MBA?"
    ]

    for msg in tests:
        result = bot.get_response(msg)
        print(f"\n  Q: {msg}")
        print(f"  Intent: {result['intent']} (confidence: {result['confidence']})")
        print(f"  A: {result['response'][:100]}...")

    print("\n" + "=" * 50)
    print("  Run app.py to start the server.")
    print("=" * 50)
