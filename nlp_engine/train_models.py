import json
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
import sklearn_crfsuite

def word2features(sent, i):
    word = sent[i]
    features = {
        'bias': 1.0,
        'word.lower()': word.lower(),
        'word[-3:]': word[-3:],
        'word[-2:]': word[-2:],
        'word.isupper()': word.isupper(),
        'word.istitle()': word.istitle(),
        'word.isdigit()': word.isdigit(),
    }
    if i > 0:
        word1 = sent[i-1]
        features.update({
            '-1:word.lower()': word1.lower(),
            '-1:word.istitle()': word1.istitle(),
            '-1:word.isupper()': word1.isupper(),
        })
    else:
        features['BOS'] = True

    if i < len(sent)-1:
        word1 = sent[i+1]
        features.update({
            '+1:word.lower()': word1.lower(),
            '+1:word.istitle()': word1.istitle(),
            '+1:word.isupper()': word1.isupper(),
        })
    else:
        features['EOS'] = True

    return features

def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]

def sent2labels(sent):
    return [label for token, label in sent]

def sent2tokens(sent):
    return [token for token, label in sent]

def train_and_save():
    train_data_path = 'data/training_data.json'
    if not os.path.exists(train_data_path):
        print(f"Error: {train_data_path} not found. Run generate_data.py first.")
        return

    with open(train_data_path, 'r') as f:
        data = json.load(f)
        
    texts = [item['text'] for item in data]
    intents = [item['intent'] for item in data]
    
    # Intent SVM
    print("Training Intent Classifier (SVM)...")
    intent_clf = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1,2))),
        ('clf', SVC(kernel='linear', probability=True))
    ])
    intent_clf.fit(texts, intents)
    
    # NER CRF
    print("Training NER Model (CRF)...")
    X_crf = [sent2features(item['tokens']) for item in data]
    y_crf = [item['tags'] for item in data]
    
    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',
        c1=0.1,
        c2=0.1,
        max_iterations=100,
        all_possible_transitions=True
    )
    crf.fit(X_crf, y_crf)
    
    # Save models
    os.makedirs('models', exist_ok=True)
    joblib.dump(intent_clf, 'models/intent_clf.pkl')
    joblib.dump(crf, 'models/ner_crf.pkl')
    print("Models saved in models/")

if __name__ == "__main__":
    train_and_save()
