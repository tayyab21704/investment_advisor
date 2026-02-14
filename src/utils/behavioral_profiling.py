from typing import List, Dict

# 🚨 Phase 1: Utilities
# File: src/utils/behavioral_profiling.py

BEHAVIORAL_QUESTIONS = [
    {
        "id": 1,
        "question": "How would you react to a 20% drop in your portfolio value over a month?",
        "options": {
            "1": "Panic and sell everything (Risk-Averse)",
            "2": "Worry but hold (Moderate)",
            "3": "See it as a buying opportunity (Aggressive)"
        }
    },
    {
        "id": 2,
        "question": "What is your primary investment goal?",
        "options": {
            "1": "Capital Preservation (Risk-Averse)",
            "2": "Steady Income (Moderate)",
            "3": "Maximum Growth (Aggressive)"
        }
    },
    {
        "id": 3,
        "question": "How much of your monthly surplus are you willing to put into 'high-risk' assets like crypto?",
        "options": {
            "1": "0-5% (Conservative)",
            "2": "5-15% (Moderate)",
            "3": "15%+ (Aggressive)"
        }
    }
]

def calculate_behavioral_risk_score(answers: List[int]) -> int:
    """
    Calculates a risk score from 1-10 based on behavioral answers.
    Each answer is expected to be 1, 2, or 3.
    """
    if not answers:
        return 5 # Neutral default
    
    total_score = sum(answers)
    max_possible = len(answers) * 3
    min_possible = len(answers) * 1
    
    # Scale from min-max to 1-10
    # Normalized score: (total - min) / (max - min) * 9 + 1
    if max_possible == min_possible:
        return 5
        
    normalized = (total_score - min_possible) / (max_possible - min_possible)
    risk_score = round(normalized * 9 + 1)
    
    return max(1, min(10, risk_score))
