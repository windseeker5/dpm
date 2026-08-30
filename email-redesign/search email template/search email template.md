# Recherche — Templates d'email transactionnels sur GitHub

*Recherche faite le 2026-08-26. Objectif : trouver des templates d'email transactionnels
(facture, reçu, preuve d'inscription, confirmation) déjà testés dans les clients email,
propres et légers — pour ne pas refaire un design à partir de zéro.*

---

## Conclusion en une ligne

**Prends [ActiveCampaign/postmark-templates](https://github.com/ActiveCampaign/postmark-templates).**
C'est la seule collection qui couvre exactement tes cas (reçu, facture, relance de paiement,
inscription, invitation), en MIT, avec dark mode et version texte déjà écrite.
Utilise [Cerberus](https://github.com/TedGoas/Cerberus) comme référence de structure si tu
veux ton propre layout, et [caniemail.com](https://www.caniemail.com/) comme table de
support CSS par client.

---

## Le shortlist

| Repo | ⭐ | Ce que c'est | Verdict |
|---|---|---|---|
| **[ActiveCampaign/postmark-templates](https://github.com/ActiveCampaign/postmark-templates)** | 3.2k | 11 templates transactionnels × 3 layouts. MIT. | **À prendre** |
| [TedGoas/Cerberus](https://github.com/TedGoas/Cerberus) | 5.1k | 3 squelettes de layout en tables HTML pures, très commentés | Le socle si tu fais ton design |
| [leemunroe/responsive-html-email-template](https://github.com/leemunroe/responsive-html-email-template) | 13.7k | Un seul fichier, un CTA, rien d'autre. MIT. | Minimum viable — trop pauvre pour une facture |
| [sendgrid/email-templates](https://github.com/sendgrid/email-templates) | 849 | Sets « paste » / « dynamic » / use-cases. MIT. | Plan B, moins soigné |
| [mailgun/transactional-email-templates](https://github.com/mailgun/transactional-email-templates) | 6.9k | 3 templates : action, alerte, billing. MIT. | Populaire mais daté (~2015), pas de dark mode. Lis juste son `billing.html` |
| [mjmlio/mjml](https://github.com/mjmlio/mjml) | 18.2k | Langage de balisage → HTML email. MIT. Node requis (ou API, ou `mjml-browser`) | Un framework, pas des templates |
| [maizzle/framework](https://github.com/maizzle/framework) | 1.6k | Vite + Tailwind pour l'email. MIT. Voir [`maizzle/starter-postmark`](https://github.com/maizzle/starter-postmark) | Idem — build Node |
| `Mail-Template/Templates` | 0 | 3 templates, MIT | À éviter : zéro traction, aucune preuve de test client |

---

## Pourquoi Postmark gagne — vérifié dans le repo, pas juste dans le README

Les 11 templates disponibles :

| Ton besoin | Template |
|---|---|
| Facture | `invoice` |
| Reçu de paiement | `receipt` |
| Preuve d'inscription | `welcome` |
| Invitation | `user-invitation` |
| Relance de paiement / échec CB | `dunning` |
| Réinitialisation mot de passe | `password-reset`, `password-reset-help` |
| Notification | `comment-notification` |
| Fin d'essai | `trial-expiring`, `trial-expired` |
| Squelette vide | `example` |

Chacun existe en 3 layouts : **`basic`** (le plus neutre, celui à prendre),
`basic-full` (fond pleine largeur), `plain` (quasi sans style).
Et en 2 versions : `templates/` (CSS dans un `<style>`) et `templates-inlined/`
(CSS déjà inliné — prends celle-là si tu ne veux pas d'étape d'inlining).

**Ce que j'ai confirmé en ouvrant les fichiers :**

- Chaque template est un **document HTML complet et autonome** (`content.html`,
  ~575 lignes pour la facture) — pas un fragment à assembler.
- **La version texte est déjà écrite** (`content.txt` à côté de chaque `content.html`).
  Ton multipart `text/plain` est donc déjà fait. C'est rare et c'est précieux.
- Structure correcte : tables imbriquées, `role="presentation"` partout,
  `<meta name="x-apple-disable-message-reformatting">`,
  `<meta name="color-scheme" content="light dark">`.
- **Vrai dark mode** : un bloc `@media (prefers-color-scheme: dark)` complet,
  plus deux breakpoints responsive (500px et 600px).
- Placeholders en Mustache : `{{invoice_id}}`, `{{amount}}`, `{{total}}`,
  `{{due_date}}`, `{{action_url}}`, `{{support_email}}`… et des boucles
  `{{#each invoice_details}}` pour les lignes de facture.

**Deux réserves honnêtes :**

1. **Le repo est figé depuis le 2022-08-25** (dernier commit). Pas grave pour du HTML
   email — ça ne pourrit pas, Outlook n'a pas bougé — mais n'attends aucune mise à jour.
2. **Il y a un `@import` Google Fonts (Nunito Sans)** en haut du `<style>`. À remplacer
   par une stack de polices système. Une webfont comme *seule* police est un piège :
   la moitié des clients l'ignorent.

---

## Si tu l'intègres — la marche à suivre

1. **Garde 4 templates au départ**, le reste est du bruit : `invoice`, `receipt`,
   `welcome`, `user-invitation`. Prends la variante `basic`.
2. **Convertis Mustache → Jinja2** : `{{variable}}` reste identique tel quel. Seules les
   sections changent : `{{#each invoice_details}}` → `{% for ligne in invoice_details %}`.
   C'est le seul endroit non trivial.
3. **Extrais un layout partagé** (`_email_base.html`) + un partial par template. Le
   `<head>`, les media queries, le bloc dark mode et le footer sont **identiques** dans
   les 4 — ne duplique pas 575 lignes quatre fois.
4. **Mets les couleurs de marque dans un seul bloc de variables** en haut du layout,
   pas éparpillées dans 400 `style=""`.
5. **Remplace l'`@import` de police** par `font-family: -apple-system, "Segoe UI", Roboto,
   Helvetica, Arial, sans-serif;`.
6. **Inline le CSS** au build ou à l'envoi (Premailer côté Python) — ou prends directement
   `templates-inlined/` et oublie l'étape.

---

## Les règles de base du HTML email (ce qui n'a pas changé)

- **Tables imbriquées, pas de `<div>`, pas de flexbox, pas de grid.** Outlook desktop
  utilise le moteur de rendu de Word. Ce n'est pas un navigateur.
- **CSS inliné** dans des `style=""`. Les `<style>` en `<head>` sont supprimés par
  certains clients (dont Gmail dans certains contextes).
- **Largeur ~600px max**, une seule colonne pour du transactionnel.
- **Toujours un `text/plain` en multipart.** Un transactionnel HTML-seul se fait
  pénaliser en délivrabilité.
- **Pas de logo en `background-image`** — Outlook l'ignore. `<img>` avec `alt` et
  dimensions explicites.
- **Pas de webfont comme seule police** — fallback système obligatoire.
- **Vérifie chaque propriété CSS douteuse sur [caniemail.com](https://www.caniemail.com/)**
  avant de l'utiliser. C'est le « Can I Use » de l'email, et c'est ce qui a remplacé
  l'Email Standards Project (mort depuis longtemps).

**À noter :** Google ne publie aucun format ou template d'email. Ce qui existe, ce sont
les [Gmail schemas / annotations](https://developers.google.com/gmail/markup) — du JSON-LD
qu'on ajoute à l'email pour que Gmail affiche des cartes riches (confirmation de commande,
réservation, colis). C'est un complément à ton HTML, pas un design.

---

## Le test qui compte

Le rendu dans un navigateur ne prouve rien. Envoie les templates à un compte de test et
ouvre-les dans, au minimum :

- **Outlook desktop** (le plus cassant — moteur Word)
- **Gmail web** + **Gmail Android** (Gmail retire certains CSS)
- **Apple Mail iOS** (et vérifie le dark mode ici)
- **Outlook mobile** (inverse le dark mode différemment d'Apple Mail)

Vérifie aussi que la version texte seule reste lisible et contient les mêmes montants et
mentions légales que le HTML.
