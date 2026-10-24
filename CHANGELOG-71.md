# Changelog — issue #71

## Issue #71 — build\rebuild_actualise.bat : refuse un numéro de build invalide ou déjà publié

- **Garde-fou étape 1** : `--build N` est désormais refusé, avant toute
  copie/construction/écriture, si `N` n'est pas un entier strictement
  supérieur au build courant de `version.json`, quel que soit le mode
  (avec ou sans `--publier`) — la copie vers le dossier fixe
  `C:\CCW_Share\_derniers_builds\actualise\` a lieu dans les deux cas.
  Message d'erreur indiquant le numéro demandé, le build courant et la
  règle ; code de sortie non nul.
- **`--build` sans valeur** (ou suivi d'un autre argument reconnaissable
  comme non numérique) est refusé avec un message explicite, au lieu
  d'être ignoré silencieusement (le script ne retombe plus sur le numéro
  automatique sans le dire).
- **Argument inconnu** refusé avec la liste des arguments acceptés
  (`--publier`, `--build N`), au lieu d'un simple avertissement suivi
  d'une construction sans publication.
- **Commentaire d'en-tête** décrivant `--build` mis à jour pour indiquer
  la règle de numéro strictement croissant et le refus des arguments
  invalides.
- **Essais réalisés** (PowerShell, depuis la racine du worktree) :
  refus rapides et sans écriture pour `--build 11` (égal au build
  publié), `--build 10` (inférieur), `--build abc` (non numérique),
  `--build` seul (sans valeur), `--publier --build 11` (déjà publié,
  avec publication), et un argument inconnu (`--publierX`) — les six cas
  sortent avec un code 1 avant toute construction, `version.json`
  inchangé (`git diff` vide) et rien de nouveau dans
  `installeur\output`. Essai accepté sans `--publier` avec `--build 99`
  (numéro fictif, jamais utilisé en publication) : installeur et archive
  construits avec succès, copiés dans `installeur\output\` du worktree
  et dans le dossier fixe du partage — fichiers à supprimer à la main
  par Alain. `version.json` reste inchangé dans toute cette issue
  (aucun `--publier` utilisé pendant les essais).
