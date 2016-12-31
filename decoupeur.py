#!/usr/bin/env python3
"""
    Découpeur de fichiers STL.
"""

import argparse
import struct
import svg_utils

# pylint: disable=C0103
# CONSTANTES
AXE_X = 0
AXE_Y = 1
AXE_Z = 2


def get_triangles(nom_fichier):
    """ Obtenir la liste des sommets d'un fichier binaire STL. """
    triangles = []
    triangles_append = triangles.append
    max_z, min_z = float('-inf'), float('inf')

    # Calcul des extrémités pour le fichier SVG
    min_x_svg, min_y_svg = float('inf'), float('inf')
    max_x_svg, max_y_svg = float('-inf'), float('-inf')

    try:
        f = open(nom_fichier, 'rb')
    except FileNotFoundError:
        print(">> Impossible de trouver le fichier", nom_fichier, "!")
        exit(1)

    with f:
        description = f.read(80)                                        # Lire la description
        nb_triangles = int.from_bytes(f.read(4), byteorder='little')    # Nombre de triangles

        if description.decode('ascii').startswith("solid"):
            print(">> Impossible de lire le fichier STL-ASCII", nom_fichier, "!")
            exit(1)

        for _ in range(nb_triangles):
            _ = (f.read(4), f.read(4), f.read(4))

            sommet_x = (struct.unpack('<f', f.read(4))[0], struct.unpack('<f', f.read(4))[0], struct.unpack('<f', f.read(4))[0])
            sommet_y = (struct.unpack('<f', f.read(4))[0], struct.unpack('<f', f.read(4))[0], struct.unpack('<f', f.read(4))[0])
            sommet_z = (struct.unpack('<f', f.read(4))[0], struct.unpack('<f', f.read(4))[0], struct.unpack('<f', f.read(4))[0])

            _ = f.read(2)

            # Extrema
            max_z_sommets = max(sommet_x[2], sommet_y[2], sommet_z[2])
            min_z_sommets = min(sommet_x[2], sommet_y[2], sommet_z[2])

            max_y_sommets = max(sommet_x[1], sommet_y[1], sommet_z[1])
            min_y_sommets = min(sommet_x[1], sommet_y[1], sommet_z[1])

            max_x_sommets = max(sommet_x[0], sommet_y[0], sommet_z[0])
            min_x_sommets = min(sommet_x[0], sommet_y[0], sommet_z[0])

            # Altitudes maximale et minimale du modèle
            max_z = max_z_sommets if max_z_sommets > max_z else max_z
            min_z = min_z_sommets if min_z_sommets < min_z else min_z

            # Coordonnées de recentrage pour le SVG
            min_x_svg = min_x_sommets if min_x_sommets < min_x_svg else min_x_svg
            min_y_svg = min_y_sommets if min_y_sommets < min_y_svg else min_y_svg
            max_x_svg = max_x_sommets if max_x_sommets > max_x_svg else max_x_svg
            max_y_svg = max_y_sommets if max_y_sommets > max_y_svg else max_y_svg

            # Ajout à la liste des triangles
            triangles_append((sommet_x, sommet_y, sommet_z))

    max_x_svg += abs(min(0, min_x_svg))
    max_y_svg += abs(min(0, min_y_svg))
    return triangles, min_z, max_z, max_x_svg, max_y_svg


def gen_tranches(n, min_z, max_z):
    """ Générer n tranches entre les altitudes min_z et max_z. """
    for tranche in range(n):
        yield int(min_z + tranche * (max_z - min_z) / n)


def triangle_coupe(tranche, triangle, plan_coupe=AXE_Z):
    """ Renvoie (sommet_seul, (oppose1, oppose2)) si la tranche coupe le triangle, (False, False) sinon. """
    def est_degenere(points):
        """ Renvoie True si le triangle est dégénéré. """
        coords_axe = [p[plan_coupe] for p in points]
        return not coords_axe or coords_axe.count(coords_axe[0]) == len(coords_axe)

    # Répartition des trois points en deux ensembles
    sommets_dessus, sommets_dessous_eq = set(), set()

    for point in triangle:
        if point[plan_coupe] > tranche:
            sommets_dessus |= {point}
        else:
            sommets_dessous_eq |= {point}

    # Vérifications, tous les sommets sont du même côté ou le triangle est dégénéré
    if len(sommets_dessus) == len(triangle) or len(sommets_dessous_eq) == len(triangle) or est_degenere(triangle):
        return False, False

    # On retourne le sommet isolé puis les deux sommets opposés
    if len(sommets_dessus) < len(sommets_dessous_eq):
        return sommets_dessus, sommets_dessous_eq
    return sommets_dessous_eq, sommets_dessus


def coords_intersection(sommet_isole, sommet_oppose, tranche, plan=AXE_Z):
    """ Renvoie les coordonnées du point d'intersection entre deux sommets. """
    point = [0.0, 0.0, tranche]
    axe_connu = (tranche - sommet_isole[plan]) / (sommet_oppose[plan] - sommet_isole[plan])

    for i in range(3):
        if i != plan:
            point[i] = axe_connu * (sommet_oppose[i] - sommet_isole[i]) + sommet_isole[i]
    return point


def intersection(tranche, triangle):
    """ Renvoyer deux points d'intersection entre la tranche et le triangle. """
    ensemble_isole, ensemble_opposes = triangle_coupe(tranche, triangle)

    if ensemble_isole is False:
        return

    # Calcul des coordonnées
    for sommet_isole in ensemble_isole:
        for sommet_oppose in ensemble_opposes:
            yield coords_intersection(sommet_isole, sommet_oppose, tranche)


def lancer_decoupage(args):
    """ Lance les fonctions de découpage à l'aide des arguments. """
    liste_triangles, min_z, max_z, max_x_svg, max_y_svg = get_triangles(args.stl_model)

    # Grouper les intersections dans une liste pour dessiner.
    for i, tranche in enumerate(gen_tranches(args.slices, min_z, max_z)):
        liste_points = []
        append = liste_points.append

        for triangle in liste_triangles:
            points_intersection = [p for p in intersection(tranche, triangle)]
            if points_intersection:
                append(points_intersection)

        svg_utils.dessiner_tranche(liste_points, i + 1, max_x_svg, max_y_svg, args.dimensions, args.margin, args.stroke, args.strokeWidth, args.repertoire)


def lecteur_arguments():
    """ Lit les arguments et retourne les arguments validés. """
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--slices', type=int, default=5, choices=range(3, 61), metavar='SLICES', help="Nombre de tranches")
    parser.add_argument('-d', '--dimensions', type=int, choices=range(300, 1201), default=500, metavar='[300-1200]', help="Taille d'un côté d'une tranche")
    parser.add_argument('-m', '--margin', type=int, choices=range(0, 301), default=0, metavar='[0-300]', help="Marge minimale autour de la tranche")
    parser.add_argument('-st', '--stroke', default="black", metavar="COULEUR", help="Couleur des traits de la tranche (acceptée par SVG)")
    parser.add_argument('-stw', '--strokeWidth', type=int, default=1, choices=range(1, 6), metavar="[1-5]", help="Largeur du trait de la tranche")
    parser.add_argument('-r', '--repertoire', type=str, default="tranches", metavar="DIR", help="Nom du répertoire de destination des tranches")
    parser.add_argument('stl_model', type=str, help="Fichier binaire .STL à découper")
    return parser.parse_args()

# ----------------------
# | Méthode principale |
# ----------------------

def main():
    """ Fonction principale. """
    args = lecteur_arguments()
    lancer_decoupage(args)

main()
