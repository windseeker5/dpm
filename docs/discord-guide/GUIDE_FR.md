# Guide : connecter Discord à votre activité Minipass

Minipass peut envoyer vos annonces par courriel **et** les publier automatiquement dans un salon Discord. Pour cela, il suffit de coller une petite adresse web (un « webhook ») dans les réglages de votre activité. Ce guide vous montre, étape par étape et avec des captures d'écran, comment l'obtenir.

Ça prend environ 5 minutes, même si vous n'avez jamais utilisé Discord.

## Ce dont vous avez besoin

- Un compte Discord (gratuit) — on vous montre comment en créer un si vous n'en avez pas.
- Un accès admin à votre activité dans Minipass.

---

## Étape 1 — Créer un compte Discord (si nécessaire)

> Si vous avez déjà un compte Discord, passez directement à l'**Étape 2**.

1. Allez sur **discord.com**.
2. Cliquez sur **Register** (S'inscrire).
3. Remplissez votre courriel, un nom d'utilisateur, un mot de passe et votre date de naissance.
4. Confirmez votre courriel en cliquant sur le lien que Discord vous envoie.

C'est tout — vous avez maintenant un compte Discord.

---

## Étape 2 — Créer un serveur Discord pour votre activité

Un « serveur » Discord, c'est simplement l'espace où vos participants pourront discuter et recevoir vos annonces.

1. Dans Discord, cliquez sur le **+** en bas de la colonne de gauche.

   ![Fenêtre "Create Your Server" avec le bouton Create My Own](images/01-create-server-modal.jpg)

2. Cliquez sur **Create My Own** (Créer le mien).
3. Discord vous demande pour qui est ce serveur — choisissez l'option qui vous convient (par exemple **For a club or community**).

   ![Écran demandant si le serveur est pour un club/communauté ou pour des amis](images/02-server-type.jpg)

4. Donnez un nom à votre serveur — idéalement le nom de votre activité (ex. : « Hockey du mardi »).

   ![Champ pour nommer le serveur, avec le bouton Create](images/03-name-server.jpg)

5. Cliquez sur **Create**. Votre serveur est prêt !

   ![Serveur nouvellement créé avec le message de bienvenue](images/04-server-created.jpg)

---

## Étape 3 — Ouvrir les paramètres du serveur

1. Cliquez sur le **nom de votre serveur** en haut à gauche, puis sur **Server Settings** (Paramètres du serveur).

   ![Menu du serveur avec l'option Server Settings](images/05-server-menu.jpg)

2. Dans le menu qui s'ouvre à gauche, repérez la section **APPS**, puis cliquez sur **Integrations**.

   ![Menu des paramètres du serveur avec Integrations sous la section APPS](images/06-server-settings-sidebar.jpg)

---

## Étape 4 — Créer le webhook

C'est l'étape la plus importante : le webhook est l'adresse que Minipass utilisera pour publier vos annonces dans Discord.

1. Sur la page **Integrations**, cliquez sur **Create Webhook**.

   ![Page Integrations avec le bouton Create Webhook](images/07-integrations-tab.jpg)

2. Discord crée un webhook avec un nom par défaut (souvent « Spidey Bot ») et le branche sur le salon **#general**.

   ![Webhook créé par défaut avec son nom et son salon](images/08-webhook-created-default.jpg)

3. Renommez-le — par exemple « Minipass » — pour vous y retrouver facilement. Une barre apparaît en bas ; cliquez sur **Save Changes**.

   ![Webhook renommé "Minipass" avec la barre Save Changes](images/09-webhook-renamed.jpg)

4. Cliquez sur **Copy Webhook URL**. L'adresse est copiée dans votre presse-papier — vous n'avez pas besoin de la voir ni de la retaper.

   ![Bouton Copy Webhook URL](images/10-copy-webhook-url.jpg)

> ⚠️ **Important :** cette adresse fonctionne comme un mot de passe. Ne la partagez jamais publiquement (courriel, site web, réseaux sociaux) — n'importe qui la possédant pourrait publier des messages dans votre salon Discord.

---

## Étape 5 (optionnelle) — Copier le lien d'invitation

Si vous voulez aussi que vos participants puissent rejoindre votre serveur Discord, copiez le lien d'invitation :

1. Cliquez sur l'icône **Invite** en haut de la liste des salons.
2. En bas de la fenêtre, cliquez sur **Copy** à côté du lien d'invitation.

   ![Fenêtre d'invitation avec le lien et le bouton Copy](images/11-invite-link.jpg)

Ce lien est différent du webhook — celui-ci sert seulement à faire *entrer des gens* dans votre serveur, pas à publier des annonces.

---

## Étape 6 — Coller l'adresse dans Minipass

1. Dans Minipass, ouvrez votre activité en mode édition.
2. Activez l'interrupteur **This activity has a Discord server**.
3. Collez l'adresse copiée à l'étape 4 dans le champ **Webhook URL**.
4. (Optionnel) Collez le lien d'invitation copié à l'étape 5 dans le champ **Discord invite link**.
5. Cliquez sur **Test** pour envoyer un message d'essai dans votre serveur Discord, puis enregistrez.

   ![Formulaire d'activité Minipass avec les champs Webhook URL et lien d'invitation remplis](images/12-minipass-activity-form.jpg)

Si le message d'essai apparaît dans votre salon Discord, tout est branché correctement.

---

## À retenir

- Le webhook est une adresse à usage privé — ne la publiez jamais.
- Vous pouvez renommer ou supprimer un webhook à tout moment depuis **Server Settings → Integrations**.
- Les annonces Minipass sont toujours envoyées par courriel ; Discord est une option en plus, pas un remplacement.
- Utilisez toujours le bouton **Test** dans Minipass après avoir collé une nouvelle adresse, pour confirmer que tout fonctionne avant d'envoyer une vraie annonce.
