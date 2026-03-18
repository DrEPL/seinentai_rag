# evaluation/load_test_set.py
import json
import os

def load_robert_test_set():
    """Charge le jeu de test basé sur l'histoire de Robert"""
    
    test_set_path = os.path.join(os.path.dirname(__file__),"data", "eval_set.json")
    
    with open(test_set_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Si c'est le format avec métadonnées
    if "test_set" in data:
        test_set = data["test_set"]
        metadata = data["metadata"]
        print(f"📊 Test set chargé: {metadata['total_questions']} questions")
        print(f"   Difficulté: {metadata['difficulty_distribution']}")
    else:
        # Format simple
        test_set = data
        print(f"📊 Test set chargé: {len(test_set)} questions")
    
    questions = [item["question"] for item in test_set]
    ground_truths = [item["ground_truth"] for item in test_set]
    
    # print("questions: ", questions)
    # print("ground_truths: ", ground_truths)
    
    return questions, ground_truths, test_set

# Utilisation
# questions, truths, full_set = load_robert_test_set()

# # Pour l'évaluation par catégorie
# easy_questions = [q for q in full_set if q["difficulty"] == "facile"]
# moral_questions = [q for q in full_set if q["category"] == "morale"]