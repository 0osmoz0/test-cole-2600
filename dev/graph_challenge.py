#!/usr/bin/env python3
"""
Challenge CTF 2600 - Graphes : plus court chemin avec Bellman-Ford.
Gère les poids négatifs et détecte les cycles absorbants.
"""
import re
import socket


def parse_matrix(text):
    """Extrait la matrice d'adjacence du texte."""
    match = re.search(r"\[\[.*?\]\]", text, re.DOTALL)
    if not match:
        return None
    return eval(match.group(0))


def has_negative_cycle_reachable(matrix, source):
    """Détecte un cycle négatif atteignable depuis source (inclut boucles sur place)."""
    n = len(matrix)
    for i in range(n):
        if matrix[i][i] < 0 and can_reach(matrix, source, i):
            return True
    return False


def bellman_ford(matrix, source, target):
    """
    Bellman-Ford pour le plus court chemin.
    Retourne: (chemin, None) si OK, (None, 'cycle absorbant') ou (None, 'pas de chemin')
    """
    n = len(matrix)
    INF = float("inf")
    dist = [INF] * n
    pred = [-1] * n
    dist[source] = 0

    # Boucle négative sur place (ex: matrix[5][5]=-5)
    if has_negative_cycle_reachable(matrix, source):
        return None, "cycle absorbant"

    # Relax edges n-1 times
    for _ in range(n - 1):
        for u in range(n):
            for v in range(n):
                w = matrix[u][v]
                if w != 0 and dist[u] != INF and dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    pred[v] = u

    # Vérifier cycle négatif au n-ième passage
    for u in range(n):
        for v in range(n):
            w = matrix[u][v]
            if w != 0 and dist[u] != INF and dist[u] + w < dist[v]:
                if can_reach(matrix, source, u):
                    return None, "cycle absorbant"

    if dist[target] == INF:
        return None, "pas de chemin"

    # Reconstruire le chemin
    path = []
    cur = target
    while cur != -1:
        path.append(cur)
        cur = pred[cur]
    path.reverse()
    return path, None


def can_reach(matrix, start, end):
    """Vérifie si on peut atteindre end depuis start (BFS)."""
    n = len(matrix)
    visited = [False] * n
    queue = [start]
    visited[start] = True
    while queue:
        u = queue.pop(0)
        if u == end:
            return True
        for v in range(n):
            if matrix[u][v] != 0 and not visited[v]:
                visited[v] = True
                queue.append(v)
    return False


def solve(text):
    """Parse le défi et retourne la réponse."""
    matrix = parse_matrix(text)
    if not matrix:
        return "erreur"

    # Extraire source et target
    src_match = re.search(r"du noeud (\d+) au noeud (\d+)", text)
    if src_match:
        source, target = int(src_match.group(1)), int(src_match.group(2))
    else:
        source, target = 0, len(matrix) - 1

    path, err = bellman_ford(matrix, source, target)
    if err:
        return err
    return " ".join(map(str, path))


def main():
    host, port = "ctf.2600.eu", 7780
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((host, port))

    while True:
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                return
            data += chunk
            text = data.decode("utf-8", errors="ignore")
            print(text, end="")
            if b">" in data:
                break

        answer = solve(text)
        print(f"Réponse: {answer}")
        s.send((answer + "\n").encode())


if __name__ == "__main__":
    main()
