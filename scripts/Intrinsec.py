import cv2
import cv2.aruco as aruco
import numpy as np
import sys

# =================================================================
# 1. CONFIGURATION (À CHANGER POUR CHAQUE CAMÉRA)
# =================================================================
# ⚠️ Modifie ces 3 lignes selon la caméra que tu calibres !
CHEMIN_VIDEO = r"C:\Users\theoc\Desktop\Projet_SYSMER_2A\Test\Intrin_air1_1.avi"  # <-- Ta vidéo à analyser
FICHIER_K_OUT = r"../donnees_calibration/intrinseques/K2.npy"  # (ou K1.npy)
FICHIER_D_OUT = r"../donnees_calibration/intrinseques/D2.npy"  # (ou D1.npy)

SEUIL_RMS = 2.0
NB_IMAGES_REQUISES = 20
INTERVALLE_FRAMES = 45 # Extrait une image toutes les 30 frames (environ 1 seconde)

# --- Paramètres Physiques ---
L, S = 0.088, 0.028
COL, LIG = 6, 6

# L'ordre magique qui a corrigé ton RMS
ids_mire = np.array([
    5,   4,  3,  2,  1,  0,
   11,  10,  9,  8,  7,  6,
   17,  16, 15, 14, 13, 12,
   23,  22, 21, 20, 19, 18,
   29,  28, 27, 26, 25, 24,
   35,  34, 33, 32, 31, 30
], dtype=np.int32)

dico = aruco.getPredefinedDictionary(aruco.DICT_APRILTAG_36h11)
board = aruco.GridBoard((COL, LIG), L, S, dico, ids_mire)

params = aruco.DetectorParameters()
params.markerBorderBits = 2
params.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX
detector = aruco.ArucoDetector(dico, params)

# =================================================================
# 2. LECTURE DE LA VIDÉO ET EXTRACTION
# =================================================================
cap = cv2.VideoCapture(1)
if not cap.isOpened():
    print(f"❌ Impossible de lire {CHEMIN_VIDEO}")
    sys.exit()

obj_points, img_points = [], []
compteur = 0
frame_idx = 0

# CORRECTION : On mémorise les dimensions dès la première frame valide
# pour éviter d'utiliser une frame potentiellement corrompue en fin de vidéo.
img_size = None

print("\n" + "="*50)
print(f"🚀 CALIBRATION MONO DEPUIS VIDÉO")
print(f"👉 Analyse de : {CHEMIN_VIDEO}")
print(f"👉 Sorties prévues : {FICHIER_K_OUT} et {FICHIER_D_OUT}")
print("="*50 + "\n")

while compteur < NB_IMAGES_REQUISES:
    ret, frame = cap.read()
    if not ret:
        print("🏁 Fin de la vidéo atteinte.")
        break
        
    frame_idx += 1

    # CORRECTION : Mémorisation des dimensions à la première frame valide
    if img_size is None:
        img_size = (frame.shape[1], frame.shape[0])  # (largeur, hauteur)

    visu = frame.copy()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    corners, ids, _ = detector.detectMarkers(gray)
    
    if ids is not None:
        aruco.drawDetectedMarkers(visu, corners, ids)
        nb_tags = len(ids)
        
        # Capture automatique si on a au moins 12 tags ET que c'est la bonne frame
        if nb_tags >= 12 and frame_idx % INTERVALLE_FRAMES == 0:
            objp, imgp = board.matchImagePoints(corners, ids)
            
            if objp is not None and len(objp) > 0:
                obj_points.append(objp)
                img_points.append(imgp)
                compteur += 1
                
                print(f"📸 Image extraite {compteur}/{NB_IMAGES_REQUISES} (Frame {frame_idx})")
                
                # Petit flash blanc pour confirmer la capture
                visu[:] = 255
    
    cv2.putText(visu, f"Captures: {compteur}/{NB_IMAGES_REQUISES}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Lecture Video", cv2.resize(visu, (1280, 720)))
    
    # Vitesse de lecture (30ms = vitesse normale)
    if cv2.waitKey(30) & 0xFF == ord('q'):
        print("⏹️ Analyse interrompue.")
        break

cap.release()
cv2.destroyAllWindows()

# =================================================================
# 3. CALCUL MATHÉMATIQUE
# =================================================================
if len(obj_points) >= 10:
    print("\n⚙️ Calcul du modèle de lentille en cours...")

    # CORRECTION : On utilise img_size mémorisé proprement, et non frame.shape
    # qui pouvait pointer vers une frame invalide (ret=False) en fin de vidéo.
    if img_size is None:
        print("❌ Aucune frame valide lue. Impossible de calibrer.")
        sys.exit()

    # Calcul avec le modèle étendu pour récupérer les incertitudes
    rms, K, D, rvecs, tvecs, stdInt, stdExt, perViewErrs = cv2.calibrateCameraExtended(
        obj_points, img_points, img_size, None, None
    )
    
    print("\n" + "="*40)
    print(f"🎯 RÉSULTAT RMS GLOBAL : {rms:.4f} pixels")
    print("="*40)
    
    # Affichage des incertitudes sur les paramètres intrinsèques
    print("\n📊 INCERTITUDES SUR LES PARAMÈTRES (Écarts-types) :")
    print(f"Incertitude Focale (fx, fy) : +/- {stdInt[0][0]:.4f}, +/- {stdInt[1][0]:.4f} pixels")
    print(f"Incertitude Centre optique (cx, cy) : +/- {stdInt[2][0]:.4f}, +/- {stdInt[3][0]:.4f} pixels")
    
    # Calcul et affichage des erreurs par image
    erreur_moy_par_image = np.mean(perViewErrs)
    erreur_max_par_image = np.max(perViewErrs)
    print(f"Erreur moyenne par image : {erreur_moy_par_image:.4f} px (Max: {erreur_max_par_image:.4f} px)")
    # ------------------------------------------------------------------------------

    if rms <= SEUIL_RMS:
        np.save(FICHIER_K_OUT, K)
        np.save(FICHIER_D_OUT, D)
        # Enregistrement des incertitudes pour un éventuel bilan global
        np.save(FICHIER_K_OUT.replace(".npy", "_std.npy"), stdInt)
        np.save(FICHIER_D_OUT.replace(".npy", "_std.npy"), stdInt)
        print(f"✅ SUCCÈS ! {FICHIER_K_OUT}, {FICHIER_D_OUT} et les fichiers d'incertitudes (_std.npy) ont été générés.")
    else:
        print(f"❌ ÉCHEC : Le RMS est trop élevé (> {SEUIL_RMS}).")
        print("💡 La vidéo manque de diversité (bords, inclinaisons) ou est trop floue.")
else:
    print(f"❌ Pas assez d'images valides ({len(obj_points)} sur 10 minimum).")