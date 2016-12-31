#!/usr/bin/env python3
"""
    Utilitaire de fonctions SVG.
"""

import os
import errno

# pylint: disable=C0103
# ---------------------------
# | Méthodes non-graphiques |
# ---------------------------

def extremums_intersections(points):
    """ Détermine les extrémités du fichier SVG. """
    min_x_svg, min_y_svg = float('inf'), float('inf')
    max_x_svg, max_y_svg = float('-inf'), float('-inf')

    for couple_points in points:
        for (x_svg, y_svg, _) in couple_points:
            min_x_svg = x_svg if x_svg < min_x_svg else min_x_svg
            min_y_svg = y_svg if y_svg < min_y_svg else min_y_svg
            max_x_svg = x_svg if x_svg > max_x_svg else max_x_svg
            max_y_svg = y_svg if y_svg > max_y_svg else max_y_svg

    return min_x_svg, max_x_svg, min_y_svg, max_y_svg


def rectifier_negatifs(points, axe_1=0, axe_2=1):
    """ Recadrer les coordonnées négatives. """
    min_x_svg, max_x_local, min_y_svg, max_y_local = extremums_intersections(points)

    if min_x_svg < 0 or min_y_svg < 0:
        min_x_svg, min_y_svg = abs(min(0, min_x_svg)), abs(min(0, min_y_svg))

        for couple_points in points:
            for point in couple_points:
                point[axe_1] += min_x_svg
                point[axe_2] += min_y_svg

    return max_x_local + min_x_svg, max_y_local + min_y_svg


def rectifier_rapport(points, max_x_svg, max_y_svg, max_x_local, max_y_local,
                      taille_x, taille_y, marge, axe_1=0, axe_2=1):
    """ Recadrer les points pour qu'ils entrent dans le SVG. """
    max_x_local = (taille_x - (max_x_local * taille_x / max_x_svg)) / 2
    max_y_local = (taille_y - (max_y_local * taille_y / max_y_svg)) / 2

    for couple_points in points:
        for point in couple_points:
            point[axe_1] = point[axe_1] * taille_x / max_x_svg + marge + max_x_local
            point[axe_2] = point[axe_2] * taille_y / max_y_svg + marge + max_y_local


def make_sure_path_exists(path):
    """ Crée le dossier 'path' s'il n'existe pas. """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

# -----------------------
# | Méthodes graphiques |
# -----------------------

def svg_init(taille_x, taille_y, marge):
    """ Renvoie l'en-tête d'un fichier SVG. """
    x_marge, y_marge = taille_x + marge * 2, taille_y + marge * 2
    return '<svg width="{0}" height="{1}">'.format(x_marge, y_marge)


def svg_close():
    """ Renvoie la balise fermante du document SVG. """
    return "</svg>"


def svg_point(x, y, epaisseur=2, stroke="", stroke_width="1", fill="black"):
    """ Dessine un point. """
    return '''<circle
        cx="{0}" cy="{1}" r="{2}"
        stroke="{3}" stroke-width="{4}"
        fill="{5}" />'''.format(x, y, epaisseur, stroke, stroke_width, fill)


def svg_ligne(x1, y1, x2, y2, stroke="black", stroke_width="1"):
    """ Dessine une ligne entre (x1, y1) et (x2, y2). """
    return '''<line
        x1="{}" y1="{}"
        x2="{}" y2="{}"
        stroke-linecap="round" style="stroke: {}; stroke-width: {};"
        />'''.format(x1, y1, x2, y2, stroke, stroke_width)


def dessiner_tranche(points, n_tranche, max_x_svg, max_y_svg, taille=500,
                     marge=0, stroke="black", stroke_width=1, directory="tranches"):
    """ Dessine une tranche à partir des points d'intersection. """
    max_x_local, max_y_local = rectifier_negatifs(points)
    rectifier_rapport(points, max_x_svg, max_y_svg, max_x_local, max_y_local,
                      taille, taille, marge)

    # Si le dossier n'existe pas, on le crée
    make_sure_path_exists(directory)

    with open(str(directory) + "/tranche_{}.svg".format(n_tranche), 'w') as f:
        print(svg_init(taille, taille, marge), file=f)

        for couple_points in points:
            point_1 = couple_points[0]
            point_2 = couple_points[1]
            print(svg_ligne(point_1[0], point_1[1], point_2[0], point_2[1], stroke, stroke_width), file=f)

        print(svg_close(), file=f)

    print("Tranche", n_tranche, "finie.")
