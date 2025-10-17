# Plan de Test et Amélioration - Système de Sondage

## Objectif
Tester et améliorer le flux complet du système de sondage du début à la fin pour assurer une expérience utilisateur optimale.

---

## Informations de Connexion (Pour Tests)
```
Email: kdresdell@gmail.com
Mot de passe: admin123
URL: http://localhost:5000
```

---

## Méthodologie de Test

### ⚠️ IMPORTANT: Utilisation de Playwright MCP
**TOUJOURS utiliser le serveur MCP Playwright pour les tests!**

Chaque fois qu'un bug est découvert ou qu'une amélioration est nécessaire:
1. ✅ Utiliser Playwright MCP pour naviguer dans l'application
2. ✅ Se connecter avec les identifiants ci-dessus
3. ✅ Reproduire le problème/tester le flux complet
4. ✅ Vérifier que la correction fonctionne via Playwright
5. ✅ NE JAMAIS demander à l'utilisateur de tester manuellement

---

## Flux Complet à Tester

### Phase 1: Création du Sondage
**Objectif**: Créer un sondage pour une activité

#### Étapes:
1. Se connecter à http://localhost:5000/login
   - Email: kdresdell@gmail.com
   - Password: admin123

2. Naviguer vers la page Sondages
   - URL: http://localhost:5000/surveys
   - Vérifier: Page se charge correctement

3. Cliquer sur "Quick Survey" (Sondage Rapide)
   - Vérifier: Modal s'ouvre correctement
   - Vérifier: Styles Bootstrap (modal-blur, centré)

4. Sélectionner le modèle français
   - Modèle: "Sondage d'Activité - Simple (questions)"
   - Vérifier: Aperçu fonctionne (bouton Preview)
   - Vérifier: 8 questions s'affichent avec les options

5. Remplir le formulaire
   - Nom du sondage: "Test Sondage [Date]"
   - Activité: Sélectionner "Surf Sess" ou une activité active
   - Vérifier: Bouton "Create Survey" s'active

6. Créer le sondage
   - Cliquer "Create Survey"
   - Vérifier: UN SEUL modal (pas de double modal)
   - Vérifier: Message de succès vert
   - Vérifier: Redirigé vers /surveys

#### Points de Vérification:
- ✅ Pas d'alertes JavaScript natives
- ✅ Modal Bootstrap professionnel
- ✅ Tous les champs requis validés
- ✅ Pas d'erreurs de formulaire
- ✅ Sondage créé dans la base de données

---

### Phase 2: Prévisualisation du Sondage
**Objectif**: Vérifier que le sondage est configurable et prévisualisable

#### Étapes:
1. Sur la page des sondages
   - Trouver le sondage créé
   - Actions → "Preview Questions"

2. Vérifier le modal de prévisualisation
   - Vérifier: 8 questions affichées
   - Vérifier: Question 1 (Rating) montre: ⭐ 1-5 avec labels
   - Vérifier: Question 2 (Pricing) montre 5 options
   - Vérifier: Questions 3-8 affichées correctement
   - Vérifier: Badges de numéros (grands, blancs sur bleu primaire)

#### Points de Vérification:
- ✅ Modal s'ouvre immédiatement
- ✅ Toutes les questions visibles
- ✅ Échelles de notation affichées clairement
- ✅ Pas de placeholders vides ("Option 1", "Option 2")

---

### Phase 3: Envoi des Invitations
**Objectif**: Envoyer les invitations par email sans erreurs

#### Étapes:
1. Sur la page des sondages
   - Actions → "Send Invitations"
   - Vérifier: Modal s'ouvre avec effet blur

2. Confirmer l'envoi
   - Cliquer "Send Invitations"
   - Vérifier: Modal se ferme
   - Vérifier: Message de succès s'affiche

3. Vérifier le message de succès
   - ✅ Message ROUGE si échec
   - ✅ Message VERT si succès
   - ✅ Compte correct de participants
   - ✅ Pas de "0 participants" si des emails envoyés

4. Vérifier les logs d'email
   ```sql
   SELECT datetime(timestamp, 'localtime'), to_email, subject, result, error_message
   FROM email_log
   WHERE template_name LIKE '%survey%'
   ORDER BY timestamp DESC
   LIMIT 5
   ```
   - Vérifier: Result = "SENT"
   - Vérifier: error_message = NULL
   - Vérifier: Pas d'entrées "FAILED" pour les emails réussis

5. Vérifier l'email reçu
   - Ouvrir boîte email: kdresdell@gmail.com
   - Vérifier: Email reçu avec sujet en français
   - Vérifier: Design professionnel (Tabler.io)
   - Vérifier: Lien du sondage fonctionne

#### Points de Vérification:
- ✅ Emails envoyés sans erreur Python
- ✅ Pas d'erreur SQLAlchemy (detached instance)
- ✅ Pas d'erreur UnboundLocalError
- ✅ Email_log montre SENT uniquement (pas de FAILED)
- ✅ Template email en français
- ✅ Logo de l'organisation chargé

---

### Phase 4: Répondre au Sondage
**Objectif**: Tester l'expérience du participant

#### Étapes:
1. Cliquer sur le lien dans l'email
   - Vérifier: Page du sondage se charge
   - Vérifier: Titre en français
   - Vérifier: 8 questions affichées

2. Tester les questions de notation (Rating)
   - Question 1: Satisfaction globale
   - Vérifier: Boutons radio avec ⭐ 1-5
   - Vérifier: Labels français affichés
   - Vérifier: Peut sélectionner une note
   - Vérifier: Validation "required" fonctionne

3. Tester les questions à choix multiples
   - Question 2: Prix justifié
   - Vérifier: 5 options affichées
   - Vérifier: Texte en français correct
   - Vérifier: Peut sélectionner une option

4. Tester les questions textuelles (open-ended)
   - Question 6-7: Commentaires
   - Vérifier: Zone de texte fonctionne
   - Vérifier: Limite de caractères (300)
   - Vérifier: Questions optionnelles fonctionnent

5. Soumettre le sondage
   - Remplir toutes les questions requises
   - Cliquer "Submit" / "Soumettre"
   - Vérifier: Message de confirmation
   - Vérifier: Ne peut pas soumettre deux fois

#### Points de Vérification:
- ✅ Questions de notation affichent les boutons radio
- ✅ Pas de champs vides/invisibles
- ✅ Barre de progression fonctionne
- ✅ Validation des champs requis
- ✅ Soumission enregistrée dans survey_response

---

### Phase 5: Visualisation des Résultats
**Objectif**: Voir les résultats du sondage

#### Étapes:
1. Page admin des sondages
   - Actions → "View Results"
   - Vérifier: Page des résultats se charge

2. Vérifier les statistiques
   - Vérifier: Nombre de réponses correctes
   - Vérifier: Graphiques affichés (si implémenté)
   - Vérifier: Réponses textuelles visibles

3. Export des résultats (si disponible)
   - Cliquer "Export" / "Exporter"
   - Vérifier: Fichier CSV téléchargé
   - Vérifier: Données complètes dans CSV

#### Points de Vérification:
- ✅ Résultats affichés correctement
- ✅ Pourcentages calculés
- ✅ Commentaires visibles
- ✅ Export fonctionne

---

### Phase 6: Gestion du Sondage
**Objectif**: Fermer, rouvrir, supprimer un sondage

#### Étapes:
1. Fermer le sondage
   - Actions → "Close Survey"
   - Vérifier: Modal de confirmation (avec blur)
   - Confirmer
   - Vérifier: Status = "Closed"

2. Rouvrir le sondage
   - Actions → "Reopen Survey"
   - Vérifier: Status = "Active"

3. Re-envoyer les invitations
   - Actions → "Resend All Invitations"
   - Vérifier: Modal de confirmation
   - Confirmer
   - Vérifier: Emails renvoyés sans erreurs

4. Supprimer le sondage
   - Actions → "Delete Survey"
   - Vérifier: Modal de confirmation
   - Confirmer
   - Vérifier: Sondage supprimé de la liste

#### Points de Vérification:
- ✅ Routes fonctionnent: /close-survey/<id>, /reopen-survey/<id>
- ✅ Pas d'erreurs 404
- ✅ Modals avec effet blur
- ✅ Actions confirmées correctement

---

## Bugs Connus à Vérifier

### ✅ Corrigés
1. ✅ Modal sans effet blur → Ajouté `modal-blur` classe
2. ✅ 404 sur /send-invitations → Routes corrigées
3. ✅ Questions vides → Template français recréé
4. ✅ Bouton preview ne fonctionne pas → API endpoint ajouté
5. ✅ Alert JavaScript → Remplacé par modal Bootstrap
6. ✅ Formulaire ne soumet pas → JavaScript corrigé
7. ✅ Questions de notation invisibles → Rendu ajouté dans survey_form.html
8. ✅ UnboundLocalError get_setting → Import corrigé
9. ✅ SQLAlchemy detached instance → Eager loading + organization_id
10. ✅ Emails "FAILED" en log → activity=None, organization_id dans context

### À Surveiller
- Performance avec beaucoup de participants (>100)
- Emails avec pièces jointes lourdes
- Compatibilité mobile du formulaire de sondage

---

## Checklist de Test Rapide

Utiliser cette checklist avant chaque release:

```
[ ] Connexion avec kdresdell@gmail.com / admin123
[ ] Créer sondage via "Quick Survey"
[ ] Sélectionner modèle français
[ ] Preview affiche 8 questions correctement
[ ] Créer sondage → UN modal uniquement
[ ] Envoyer invitations → Message vert
[ ] Vérifier email_log: SENT, pas FAILED
[ ] Cliquer lien dans email → Sondage s'ouvre
[ ] Questions rating affichent ⭐ 1-5
[ ] Soumettre sondage → Confirmation
[ ] View Results → Résultats affichés
[ ] Resend All → Emails renvoyés sans erreur
[ ] Close/Reopen → Fonctionne
[ ] Delete → Sondage supprimé
```

---

## Commandes SQL Utiles

### Vérifier les sondages
```sql
SELECT id, name, status, activity_id
FROM survey
WHERE status = 'active'
ORDER BY created_dt DESC;
```

### Vérifier les invitations envoyées
```sql
SELECT
    datetime(timestamp, 'localtime') as time,
    to_email,
    subject,
    result,
    error_message
FROM email_log
WHERE template_name LIKE '%survey%'
ORDER BY timestamp DESC
LIMIT 10;
```

### Vérifier les réponses
```sql
SELECT
    sr.id,
    u.email,
    sr.completed,
    datetime(sr.invited_dt, 'localtime') as invited,
    datetime(sr.completed_dt, 'localtime') as completed
FROM survey_response sr
JOIN user u ON sr.user_id = u.id
WHERE sr.survey_id = [SURVEY_ID]
ORDER BY sr.created_dt DESC;
```

### Compter les participants
```sql
SELECT
    COUNT(*) as total_passports
FROM passport
WHERE activity_id = [ACTIVITY_ID];
```

---

## Script de Test Automatisé (Playwright MCP)

### Exemple de flux complet:
```python
# 1. Naviguer vers login
navigate("http://localhost:5000/login")

# 2. Se connecter
fill("input[name='email']", "kdresdell@gmail.com")
fill("input[name='password']", "admin123")
click("button[type='submit']")

# 3. Aller aux sondages
navigate("http://localhost:5000/surveys")

# 4. Créer sondage
click("button:has-text('Quick Survey')")
select("select[name='template']", "Sondage d'Activité - Simple (questions)")
fill("input[name='name']", "Test Sondage 2025-10-15")
select("select[name='activity']", "Surf Sess")
click("button:has-text('Create Survey')")

# 5. Vérifier succès
expect("div.alert-success").to_be_visible()

# 6. Envoyer invitations
click("button:has-text('Actions')")
click("a:has-text('Send Invitations')")
click("button:has-text('Send Invitations')")

# 7. Vérifier message succès vert
expect("div.alert-success").to_contain_text("invitations sent")

# 8. Vérifier pas d'erreur rouge
expect("div.alert-error").not_to_be_visible()
```

---

## Améliorations Futures à Considérer

### UX
1. Aperçu du sondage côté participant avant envoi
2. Édition de sondages actifs (avec notifications)
3. Sondages multi-langues (français/anglais)
4. Rappels automatiques pour non-répondants

### Technique
1. File d'attente d'emails (queue) pour envoi massif
2. Templates d'emails personnalisables par activité
3. Export PDF des résultats
4. Dashboard analytique avec graphiques

### Performance
1. Pagination des résultats
2. Cache des statistiques
3. Envoi d'emails par batch (100 à la fois)
4. Index sur survey_response.survey_id

---

## Notes Importantes

### Environnement de Test
- **Flask Server**: Toujours running sur localhost:5000 en mode debug
- **Base de données**: SQLite dans instance/minipass.db
- **SMTP**: mail.minipass.me:587 (configuré)
- **Email test**: kdresdell@gmail.com

### Dépendances
- Playwright MCP Server (pour tests automatisés)
- Flask en mode debug (auto-reload)
- Templates Tabler.io CSS
- Email template compilés dans templates/email_templates/

### Fichiers Clés
- Route principale: `app.py` lignes 6930-7200
- Template email: `templates/email_templates/email_survey_invitation_compiled/`
- Formulaire sondage: `templates/survey_form.html`
- Page gestion: `templates/surveys.html`
- Template français: ID 8 dans `survey_template` table

---

## Contacts & Support

**Pour problèmes techniques:**
- Vérifier les logs Flask (terminal où app.py tourne)
- Vérifier email_log dans la base de données
- Vérifier /tmp/survey_debug.log si activé

**Documentation:**
- PRD: docs/PRD.md Section 4.1.F (Automated Survey System)
- Fixes historiques: SURVEY_*.md dans le dossier racine

---

**Dernière mise à jour**: 2025-10-15
**Status**: ✅ Système fonctionnel et testé
**Version**: 1.0
