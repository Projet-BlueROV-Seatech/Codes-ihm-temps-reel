# SYSMER Tracker — Interface de Calibration et Suivi 3D

Ce dépôt contient le pipeline complet de tracking 3D du BlueROV2, réorganisé autour d'une **interface graphique (IHM)** qui orchestre toutes les étapes en un seul clic. Plus besoin de modifier les chemins dans le code ou de lancer les scripts manuellement : le lanceur gère tout.

Le principe reste le même que le pipeline précédent : YOLO détecte le robot dans chaque caméra, on triangule les deux points 2D pour reconstruire sa position en 3D, et on l'affiche en temps réel. L'IHM ajoute simplement une couche de confort pour l'utilisation sur le terrain.

>  Ce repo s'appuie sur le pipeline décrit dans le [repo YOLO](lien_vers_repo_YOLO). Si vous n'avez jamais fait la calibration, lisez d'abord ce repo pour comprendre ce que chaque étape fait.
>
>  Pour le montage physique du matériel (caméras, mire, Qualisys), voir **[README_INSTALLATION.md](README_INSTALLATION.md)**.

---

## Structure du projet

```
Codes-ihm-temps-reel-main/
│
├── Lanceur_IHM.py                  ← Point d'entrée unique — lancer ce fichier
│
├── scripts/                        → Les scripts du pipeline (lancés par l'IHM)
│   ├── Intrinsec_cam1.py           (calibration intrinsèque caméra 1)
│   ├── Intrinsec_cam2.py           (calibration intrinsèque caméra 2)
│   ├── Extrinsec.py                (calibration extrinsèque inter-caméras)
│   ├── Passage.py                  (construction des matrices P1, P2)
│   ├── Redressement.py             (calibration du plan sol)
│   └── Tracking.py                 (tracking 3D YOLO en temps réel)
│
├── donnees_calibration/            → Fichiers .npy générés par les étapes 1 à 4
│   ├── intrinseques/               (K1, D1, K2, D2)
│   ├── extrinseques/               (R_c2_c1, t_c2_c1, P1, P2)
│   └── environnement/              (R_redressement, hauteur_cam1)
│
├── modeles/
│   └── best.pt                     ← Modèle YOLO pré-entraîné sur le BlueROV2
│
└── resultats_tracking/             → Fichiers de sortie du tracking
    ├── trajectoire_robot_*.tsv     (coordonnées X, Y, Z enregistrées)
    └── erreurs_triangulation_*.npy (erreurs de reprojection par frame)
```

---

## Étape 0 — Installer Python et les dépendances

### 0.1 Installer Python

1. Rendez-vous sur **[python.org/downloads](https://www.python.org/downloads/)** et téléchargez **Python 3.10** ou **3.11** (recommandé).
2. Lancez l'installateur. ** Cochez bien "Add Python to PATH"** avant de cliquer sur "Install Now". Sans cette case cochée, rien ne fonctionnera.
3. Vérifiez que l'installation a fonctionné en ouvrant un terminal et en tapant :
   ```bash
   python --version
   ```
   Vous devriez voir quelque chose comme `Python 3.11.x`.

### 0.2 Installer les dépendances

Toutes les bibliothèques nécessaires s'installent en une seule commande :
```bash
pip install opencv-python numpy ultralytics scipy matplotlib
```

Voilà à quoi sert chaque bibliothèque :
- `opencv-python` : traitement d'image, détection ArUco, triangulation stéréo
- `numpy` : calcul matriciel (matrices de calibration, points 3D)
- `ultralytics` : YOLOv8 (détection du robot)
- `scipy` : optimisation Nelder-Mead pour la calibration extrinsèque
- `matplotlib` : affichage 3D de validation des calibrations

>  `tkinter` (utilisé par l'IHM) est inclus par défaut dans toutes les installations Python — vous n'avez pas besoin de l'installer séparément.

>  Si vous êtes sous Windows et que `pip` n'est pas reconnu, remplacez-le par `python -m pip install ...`.

---

## Ce qu'il vous faut avant de commencer

- **Deux caméras fisheye USB** branchées au PC (caméras DeepWater exploreHD dans notre cas).
- **Une mire ArUco** : un plateau 6×6 de tags `DICT_APRILTAG_36h11` (marqueurs de 8,8 cm, espacement 2,8 cm).
- **Le modèle YOLO** : le fichier `best.pt` est déjà inclus dans le dossier `modeles/`. Si vous souhaitez utiliser votre propre modèle, remplacez simplement ce fichier en gardant le même nom.

>  **Angle entre les caméras :** l'angle entre les axes optiques des deux caméras ne doit pas dépasser 90°. Au-delà, la calibration extrinsèque échoue. Voir [README_INSTALLATION.md](README_INSTALLATION.md) pour le montage physique.

---

## Lancer l'interface

Tout part d'un seul fichier. Depuis un terminal, placez-vous à la racine du projet et lancez :

```bash
python Lanceur_IHM.py
```

Une fenêtre s'ouvre avec 6 boutons, un par étape du pipeline. **Exécutez-les dans l'ordre, de haut en bas.** Fermez toujours la fenêtre d'un script avant de passer au suivant.

---

## Étape 1a et 1b — Calibration Intrinsèque (une fois par caméra)

**Boutons :** `1a. Calibration Intrinsèque (Cam 1)` puis `1b. Calibration Intrinsèque (Cam 2)`

L'IHM vous demande l'index de chaque caméra avant de lancer le script. Si vous ne connaissez pas les index, consultez la section [Trouver les index de vos caméras](#trouver-les-index-de-vos-caméras) plus bas.

**Ce que fait cette étape :** elle calcule les paramètres optiques de chaque caméra (focale, centre optique, distorsion) à partir du flux vidéo en direct avec la mire.

**Procédure :**
1. Cliquez sur le bouton et entrez l'index de la caméra dans la fenêtre de dialogue.
2. Le script s'ouvre et commence à analyser le flux.
3. Déplacez la mire lentement devant la caméra en couvrant tous les coins de l'image et en l'inclinant sous différents angles. Évitez tout mouvement rapide — le flou empêche la détection des AprilTags.
4. Le script extrait automatiquement des images toutes les 45 frames. À la fin, il affiche le **RMS de reprojection** :
   -  `RMS < 1.5` → calibration acceptée. `K1.npy` et `D1.npy` sont sauvegardés dans `donnees_calibration/intrinseques/`.
   -  `RMS ≥ 1.5` → calibration rejetée. Recommencez en couvrant plus de positions différentes.

**Répétez pour la caméra 2** avec le bouton `1b`.

---

## Étape 2 — Calibration Extrinsèque

**Bouton :** `2. Calibration Extrinsèque`

L'IHM réutilise automatiquement les index de caméras renseignés aux étapes 1a et 1b — pas besoin de les entrer à nouveau.

**Ce que fait cette étape :** elle détermine la position et l'orientation d'une caméra par rapport à l'autre (rotation + translation inter-caméras).

**Procédure :**
1. Placez la mire dans la zone vue par les deux caméras simultanément.
2. Quand la mire est bien visible et stable, appuyez sur **ENTRÉE** dans la fenêtre de la caméra pour lancer l'analyse.
3. Le système attend que 20 ArUcos communs soient stables sur 10 frames consécutives.
4. Un graphique 3D s'affiche pour valider la position relative des deux caméras.
5. Répondez `O` dans le terminal pour sauvegarder, ou `N` pour recommencer.

Les fichiers sauvegardés dans `donnees_calibration/extrinseques/` sont : `R_c2_c1.npy`, `t_c2_c1.npy`, `c2Mc1.npy`, `wMc1.npy`, `wMc2.npy`.

---

## Étape 3 — Génération des Matrices de Projection

**Bouton :** `3. Génération des Matrices`

**Ce que fait cette étape :** à partir des matrices intrinsèques et extrinsèques, elle construit les matrices `P1` et `P2` nécessaires à OpenCV pour la triangulation.

Cliquez sur le bouton. Le script se termine en quelques secondes et génère `P1.npy` et `P2.npy` dans `donnees_calibration/extrinseques/`. Aucune interaction n'est requise.

---

## Étape 4 — Redressement du Sol

**Bouton :** `4. Redressement du Sol`

**Ce que fait cette étape :** les caméras ne regardent pas exactement vers le bas, ce qui incline les coordonnées 3D reconstruites. Cette étape calcule une rotation pour que l'axe Y corresponde à la gravité et que la hauteur affichée soit correcte.

**Procédure :**
1. Posez la mire **à plat sur le sol** du bassin (ou de la surface de test), bien horizontale, dans le champ de la caméra 1.
2. Cliquez sur le bouton.
3. Appuyez sur **ENTRÉE** dans la fenêtre pour lancer l'analyse de stabilité.
4. Un graphique 3D s'affiche avec les axes du nouveau repère monde et la hauteur des caméras.
5. Répondez `O` pour sauvegarder.

Les fichiers sauvegardés dans `donnees_calibration/environnement/` sont : `R_redressement.npy` et `hauteur_cam1.npy`.

>  **Cette étape est optionnelle.** Si les fichiers de redressement sont absents, le Tracking démarrera quand même avec le repère brut de la caméra 1 et affichera un avertissement.

---

## Étape 5 — Lancement du Tracking

**Bouton :** `5. Lancement du Tracking`

C'est le script principal. Il ouvre les deux caméras, lance YOLO sur chaque flux, triangule la position du robot et affiche tout en temps réel.

### Interface et contrôles

La fenêtre affiche :
- **En haut :** flux vidéo des deux caméras avec la bounding box YOLO.
- **En bas à gauche :** vue de dessus (plan X-Z) avec la trajectoire et les cônes de vision des caméras.
- **En bas au milieu :** vue de profil (plan Z-Y) avec la hauteur du robot.
- **En bas à droite :** coordonnées X, Y, Z en mètres, FPS, état de détection par caméra.

| Touche | Action |
|--------|--------|
| `Q` | Quitter proprement et sauvegarder le TSV |
| `ESPACE` | Mettre en pause |
| `R` | Activer / désactiver l'enregistrement dans le fichier TSV |

### Fichiers de sortie

Chaque session de tracking génère automatiquement dans `resultats_tracking/` :
- `trajectoire_robot_*.tsv` : coordonnées X, Y, Z (en mètres) avec horodatage, une ligne par frame détectée.
- `erreurs_triangulation_yolo_temps_reel.npy` : erreur de reprojection par frame (pour évaluer la qualité de la triangulation).

>  Si un pop-up d'erreur s'affiche au lancement du Tracking en disant que des fichiers de calibration sont introuvables, c'est qu'une des étapes précédentes n'a pas été complétée. Relancez les étapes manquantes dans l'ordre.

---

## Trouver les index de vos caméras

Si vous ne savez pas quel index correspond à quelle caméra, copiez ce code dans un fichier `.py` et lancez-le :

```python
import cv2

for index in range(5):
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"Caméra trouvée à l'index : {index}")
            cv2.imshow(f"Index {index}", frame)
            cv2.waitKey(2000)
        cap.release()
cv2.destroyAllWindows()
```

Chaque caméra s'affichera 2 secondes avec son index. L'IHM mémorise les index que vous entrez aux étapes 1a et 1b — ils seront réutilisés automatiquement pour toutes les étapes suivantes.

---

## Récapitulatif de l'ordre d'exécution

```
python Lanceur_IHM.py
         │
         ▼
[1a] Intrinsec_cam1.py   →  K1.npy, D1.npy  (dans donnees_calibration/intrinseques/)
[1b] Intrinsec_cam2.py   →  K2.npy, D2.npy
         │
         ▼
[2]  Extrinsec.py        →  R_c2_c1.npy, t_c2_c1.npy, ...  (dans extrinseques/)
         │
         ▼
[3]  Passage.py          →  P1.npy, P2.npy  (dans extrinseques/)
         │
         ▼
[4]  Redressement.py     →  R_redressement.npy, hauteur_cam1.npy  (dans environnement/)
         │
         ▼
[5]  Tracking.py         →  Tracking 3D en temps réel 
                             + resultats_tracking/trajectoire_robot_*.tsv
```

---

*Projet réalisé dans le cadre du module de vision par ordinateur — SeaTech, 2025-2026.*
