#!/usr/bin/env python3
"""ActualiseUI — fenêtre de choix affichée par l'application cible
(Scrabble, Rummikub, ...) quand une mise à jour d'Actualise est en
attente de validation utilisateur (présence d'``actualise_update.flag``
dans son dossier d'installation).

Compilé séparément en ``ActualiseUI.exe`` (--onefile, --noconsole).
N'est jamais importé par ``actualise.py``.
"""

import argparse
import subprocess
import tkinter as tk
from pathlib import Path


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(description="ActualiseUI — choix de mise à jour Actualise")
    analyseur.add_argument("--bat", required=True, type=str, help="Chemin absolu vers updater.bat")
    analyseur.add_argument(
        "--flag", required=True, type=str, help="Chemin absolu vers actualise_update.flag"
    )
    analyseur.add_argument(
        "--relancer",
        required=False,
        type=str,
        default=None,
        help="Chemin absolu vers l'exécutable à relancer une fois la mise à jour appliquée",
    )
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    arguments = analyser_arguments(argv)
    chemin_bat = Path(arguments.bat)
    chemin_flag = Path(arguments.flag)

    fenetre = tk.Tk()
    fenetre.title("Mise à jour disponible")
    fenetre.resizable(False, False)
    fenetre.attributes("-topmost", True)
    try:
        # "-toolwindow" : fenêtre outil Windows, sans entrée dans la
        # barre des tâches. Attribut spécifique à Windows.
        fenetre.attributes("-toolwindow", True)
    except tk.TclError:
        pass

    def plus_tard() -> None:
        fenetre.destroy()

    def mettre_a_jour() -> None:
        chemin_flag.unlink(missing_ok=True)
        commande = f'"{chemin_bat}"'
        if arguments.relancer:
            commande += f' --relancer "{arguments.relancer}"'
        subprocess.Popen(commande, shell=True)
        fenetre.destroy()

    fenetre.protocol("WM_DELETE_WINDOW", plus_tard)

    tk.Label(fenetre, text="Mise à jour disponible", font=("Segoe UI", 12, "bold")).pack(
        padx=20, pady=(20, 5)
    )
    tk.Label(fenetre, text="Le jeu va redémarrer pour appliquer la mise à jour.").pack(
        padx=20, pady=(0, 15)
    )

    cadre_boutons = tk.Frame(fenetre)
    cadre_boutons.pack(padx=20, pady=(0, 20))
    tk.Button(cadre_boutons, text="Mettre à jour", command=mettre_a_jour).pack(side=tk.LEFT, padx=5)
    tk.Button(cadre_boutons, text="Plus tard", command=plus_tard).pack(side=tk.LEFT, padx=5)

    fenetre.mainloop()


if __name__ == "__main__":
    main()
