# Script de Test du Pipeline RAG

Ce script teste automatiquement tous les composants du système RAG pour s'assurer qu'ils fonctionnent correctement.

## Utilisation

### Prérequis

Assurez-vous que les services Docker sont démarrés :

```bash
docker-compose up -d
```

### Lancement des tests

```bash
python test_pipeline.py
```

### Nettoyage après test

Pour nettoyer les données de test :

```bash
python cleanup_test.py
```

## Tests effectués

### 1. Tests individuels

- **DocumentProcessor** : Test d'extraction de texte
- **TextChunker** : Test de découpage de texte
- **VectorStore** : Test d'indexation et recherche
- **DocumentManager** : Test de gestion des documents

### 2. Test de l'Orchestrateur d'Intentions (Intent Router)

- **Classification** : Test de détection (Small Talk vs Knowledge Query)
- **Direct Response** : Vérification des réponses rapides sans RAG
- **Logs** : Suivi des intentions dans la console FastAPI

### 3. Test du pipeline complet

- Création de documents de test
- Upload vers MinIO
- Indexation automatique
- Recherche dans l'index

## Documents de test

Le script crée automatiquement 3 documents de test :

1. **intelligence_artificielle.txt** : Texte sur l'IA et le ML
2. **guide_python.txt** : Guide d'installation Python
3. **bioinformatique.txt** : Introduction à la bioinformatique

## Résultats attendus

```
🧪 DÉBUT DES TESTS DU PIPELINE RAG
==================================================
🧪 Test du DocumentProcessor...
✅ DocumentProcessor fonctionne correctement
🧪 Test du TextChunker...
✅ TextChunker fonctionne: X chunks créés
🧪 Test du VectorStore...
✅ VectorStore indexation fonctionne
✅ VectorStore recherche fonctionne: X résultats
🧪 Test du DocumentManager...
✅ DocumentManager listage: X fichiers trouvés
✅ DocumentManager statut: X fichiers, X indexés

🚀 Test du pipeline RAG complet...
📤 Upload des documents de test vers MinIO...
✅ Uploadé: intelligence_artificielle.txt
✅ Uploadé: guide_python.txt
✅ Uploadé: bioinformatique.txt
📄 3 documents de test uploadés
🔄 Indexation des documents...
📊 Rapport d'indexation:
  - Documents traités: 3
  - Indexés: 3
  - Erreurs: 0
🔍 Test de recherche...
✅ Recherche réussie: X résultats trouvés
✅ Pipeline RAG complet fonctionne !

==================================================
📊 RÉSULTATS DES TESTS
Document Processing: ✅ PASSÉ
Text Chunking: ✅ PASSÉ
Vector Store: ✅ PASSÉ
Document Manager: ✅ PASSÉ
Full Pipeline: ✅ PASSÉ

📈 Score: 5/5 tests réussis
🎉 Tous les tests sont passés ! Le pipeline RAG est opérationnel.
```

## Nettoyage

### Script `cleanup_test.py`

Le script de nettoyage permet de :

1. **Supprimer les documents de test** de MinIO
2. **Supprimer les index correspondants** de Qdrant
3. **Optionnellement remettre à zéro** complètement les collections

### Utilisation

```bash
python cleanup_test.py
```

Le script demandera confirmation avant les opérations destructives.

## Dépannage

### Erreur de connexion MinIO/Qdrant

Vérifiez que les conteneurs Docker sont démarrés :

```bash
docker-compose ps
```

### Erreur d'embeddings

Le script utilise des embeddings aléatoires pour les tests. Pour un usage réel, implémentez un vrai modèle dans `DocumentManager._generate_embeddings()`.

### Documents non indexés

Vérifiez les logs pour les erreurs spécifiques. Les causes communes :
- Format de fichier non supporté
- Erreur de parsing du document
- Problème de connexion aux services

## Extension des tests

Pour ajouter de nouveaux tests :

1. Ajoutez une fonction `test_nom_du_test()`
2. Appelez-la dans `main()`
3. Ajoutez le résultat dans le dictionnaire `results`

Exemple :

```python
def test_custom_functionality():
    # Votre test personnalisé
    return True

# Dans main()
results['custom_functionality'] = test_custom_functionality()
```