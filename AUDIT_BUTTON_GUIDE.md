# Guide d'Utilisation - Bouton d'Analyse d'Audit

## 🎯 Objectif

Cette fonctionnalité permet aux utilisateurs de visualiser rapidement l'analyse complète d'un audit directement depuis la liste des documents, sans avoir à naviguer vers une page séparée.

## 📋 Fonctionnalités

### 1. **Bouton "📊 Analyse" dans la table des documents**

Dans la page "Documents", chaque document a maintenant un bouton dédié:

```
┌─────────┬────┬────────────────┬──────────┬─────────────┬─────────────────────┐
│ ☐ Sélectionner │ ID │ Fichier      │ Standard │ Date Upload │ Actions             │
├─────────┼────┼────────────────┼──────────┼─────────────┼─────────────────────┤
│ ☐       │ 1  │ audit_2026.pdf │ ISO27001 │ 12/03/2026  │ [📊 Analyse] Suppr. │
│ ☐       │ 2  │ policy.docx    │ GDPR     │ 12/03/2026  │ [📊 Analyse] Suppr. │
└─────────┴────┴────────────────┴──────────┴─────────────┴─────────────────────┘
```

### 2. **Modale d'Analyse Interactive**

En cliquant sur le bouton "📊 Analyse", une modale s'ouvre affichant:

#### **Résumé**
- Score global (0-100)
- Statut de conformité:
  - 🟢 **Conforme** (score ≥ 80)
  - 🟡 **Partiellement Conforme** (50 ≤ score < 80)
  - 🔴 **Non Conforme** (score < 50)

#### **Violations Détectées**
Liste des violations trouvées avec:
- Nombre total de violations
- Nombre de violations critiques
- Détails de chaque violation avec type et description

Exemples de types de violations:
- `missing_procedure`: Procédure manquante
- `missing_responsibility`: Responsabilité non définie
- `no_enforcement`: Aucune application
- `missing_approval`: Approbation manquante
- `missing_review`: Révision manquante
- `incomplete_implementation`: Implémentation incomplète
- `conflicting_statements`: Déclarations contradictoires

#### **Contrôles Manquants**
Liste des contrôles de sécurité non implémentés avec:
- Nom du contrôle
- Nombre total manquant

#### **Risques Identifiés**
Liste des risques avec:
- **Niveau de sévérité**: 🔴 Critique / 🟠 Élevé / 🟡 Moyen / 🔵 Bas
- **Description du risque**
- **Implications potentielles**

#### **Recommandations**
Actions recommandées pour améliorer la conformité:
- **Titre de l'action**
- **Description détaillée**
- **Priorité** (Critique, Haute, Normale, Basse)

## 🚀 Guide d'Utilisation

### Étape 1: Accéder à la page Documents
```
Menu latéral → Documents
ou
URL directe: http://localhost:8000/documents/
```

### Étape 2: Afficher l'analyse
1. Repérez le document dont vous voulez consulter l'analyse
2. Cliquez sur le bouton **"📊 Analyse"** dans la colonne "Actions"

### Étape 3: Examiner les résultats
La modale affiche automatiquement:
- Le résumé avec score et statut
- Les violations détectées (le point clé décidant du statut)
- Les contrôles manquants
- Les risques associés
- Les recommandations pour corriger les problèmes

### Étape 4: Fermer la modale
- Cliquez sur le bouton **"Fermer"** en bas à droite
- Ou cliquez sur la **croix (×)** dans le coin haut-droit
- Ou appuyez sur **ESC** du clavier

## 📊 Interprétation des Résultats

### Score et Statut

| Score | Statut | Couleur | Signification |
|-------|--------|---------|---------------|
| 80-100 | ✅ Conforme | 🟢 Vert | Document conforme aux normes |
| 50-79 | ⚠️ Partiellement | 🟡 Orange | Améliorations nécessaires |
| 0-49 | ❌ Non Conforme | 🔴 Rouge | Violations majeures détectées |

### Priorité des Violations

Les violations sont détectées automatiquement en analysant:
1. **Procédures manquantes** → Violation majeure
2. **Responsabilités non clairement définies** → Impact moyen-haut
3. **Contrôles non appliqués** → Violation critique
4. **Manque de révisions** → Compétence résiduelle

### Risques par Sévérité

- 🔴 **CRITIQUE**: Doit être résolu immédiatement
- 🟠 **ÉLEVÉ**: Doit être adressé dans les 2 semaines
- 🟡 **MOYEN**: Doit être planifié dans les 30 jours
- 🔵 **BAS**: À considérer dans les améliorations futures

## 💡 Cas d'Usage Courants

### Cas 1: Audit Non Conforme avec Violations Critiques
```
User: "Ce document est non-conforme, comment le corriger?"
1. Cliquez sur "📊 Analyse"
2. Allez à "Violations Détectées" 
3. Identifiez les violations critiques
4. Consultez "Recommandations"
5. Implémentez les changements suggérés
```

### Cas 2: Vérifier la Progression
```
User: "Nous avons corrigé des violations, ont-elles disparu?"
1. Cliquez sur "📊 Analyse"
2. Vérifiez le nombre de violations → doit diminuer
3. Vérifiez le score → doit augmenter
4. Vérifiez les contrôles manquants → liste réduite
```

### Cas 3: Préparer une Présentation
```
User: "Je dois présenter la conformité à un client"
1. Pour chaque document important, cliquez sur "📊 Analyse"
2. Capturez les résultats (screenshot)
3. Compilez dans un rapport
4. Présentez en mettant l'accent sur les risques critiques
```

## ⚡ Performance

- **Temps de chargement**: < 1 seconde (données en cache)
- **Taille des données**: Optimisée pour performance
- **Support navigateur**: 
  - ✅ Chrome/Chromium 90+
  - ✅ Firefox 88+
  - ✅ Safari 14+
  - ✅ Edge 90+

## 🔒 Sécurité

- ✅ Authentification requise (utilisateur connecté)
- ✅ Autorisation vérifiée (utilisateur peut accéder au document)
- ✅ Données sensibles masquées selon les permissions
- ✅ Pas de stockage client (données serveur uniquement)

## 📱 Responsive Design

La modale s'adapte automatiquement à:
- 📱 Téléphones mobiles (scrollable vertical)
- 💻 Tablettes (layout optimisé)
- 🖥️ Bureaux (pleine largeur avec barre de défilement)

## 🐛 Dépannage

### "Aucune analyse disponible"
**Cause**: Aucun audit n'a été exécuté pour ce document
**Solution**: 
1. Allez à l'onglet "Audit"
2. Sélectionnez le document
3. Cliquez sur "Exécuter l'audit"
4. Attendez la fin de l'analyse
5. Revenez aux documents et cliquez à nouveau sur "Analyse"

### "Erreur lors du chargement"
**Cause**: Problème de connexion ou d'authentification
**Solution**:
1. Vérifiez votre connexion Internet
2. Vérifiez que vous êtes connecté
3. Rafraîchissez la page (F5)
4. Essayez à nouveau

### Données incomplètes
**Cause**: Analyse interrompue précédemment
**Solution**:
1. Supprimez le document
2. Re-uploadez
3. Re-exécutez l'audit
4. Consultez l'analyse

## 🔗 Relation avec d'autres Fonctionnalités

```
Documents Page
    ↓
    └─→ [📊 Analyse] Opens Modal with:
            ├─→ Violations (from violation_detector.py)
            ├─→ Score (from multi_factor_scorer.py)
            ├─→ Risks (from risk_agent.py)
            └─→ Recommendations (from recommendation_agent.py)
```

## 📞 Support

Pour toute question ou problème:
1. Consultez la documentation API: `/api/compliance/results/`
2. Vérifiez les logs: `logs/django.log`
3. Contactez l'équipe support avec:
   - Document ID
   - Statut attendu vs réel
   - Messages d'erreur exactes

## 📝 Notes Supplémentaires

### Limitation Connue
- Les analyses très longues (> 50 contrôles) peuvent nécessiter un scroll dans la modale
- Ceci est intentional pour maintenir la performance

### Données Cachées
Certaines données sensibles ne sont visibles que selon votre niveau de permission:
- Données personnelles (si applicable)
- Détails techniques sensibles
- Chemins d'accès système

### Format des Données
Les données sont retournées au format JSON par l'API:
- Parfait pour l'intégration avec d'autres systèmes
- Peut être exporter en CSV/PDF (future feature)

## ✨ Améliorations Futures

- ✅ Export PDF de l'analyse
- ✅ Partage d'analyse par email
- ✅ Historique des évolutions (avant/après corrections)
- ✅ Comparaison de plusieurs documents
- ✅ Tableau de bord de tendances

---

**Dernière mise à jour**: 12 Mars 2026
**Version**: 1.0
**Langue**: Français
