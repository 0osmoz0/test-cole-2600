#!/usr/bin/env python3
"""
Script pour résoudre le quiz web 2600 CTF.
Vous avez 2 secondes pour répondre - ce script le fait en millisecondes.

Usage:
  python web_quiz.py           # Mode requests (rapide)
  python web_quiz.py --selenium # Mode Selenium (DOM exact, plus fiable)
"""
import argparse
import re
import sys

import requests

BASE_URL = "https://ctf.2600.eu/admissions/web_quizz"


def extract_hidden_block(html):
    """Extrait le contenu du bloc div caché (display:none) en utilisant le parsing par profondeur."""
    start_marker = '<div style="display: none;">'
    start = html.find(start_marker)
    if start == -1:
        start = html.find('<div style="display: none;">')
    if start == -1:
        return None

    start += len(start_marker)
    depth = 1
    pos = start

    while depth > 0 and pos < len(html):
        next_open = html.find("<div", pos)
        next_close = html.find("</div>", pos)
        if next_close == -1:
            break
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                return html[start:next_close]
            pos = next_close + 6

    return None


def find_special_div_index(block_content):
    """Trouve l'index (0-based) du div qui se démarque (inner ou special) parmi les
    enfants directs du bloc caché. Le serveur alterne entre les deux."""
    depth = 0
    pos = 0
    idx = 0
    inner_idx = None
    special_idx = None

    while pos < len(block_content):
        open_m = re.search(r"<div(\s[^>]*)?>", block_content[pos:])
        if not open_m:
            break
        tag = open_m.group(0)
        pos += open_m.end()
        if depth == 0:
            cls_match = re.search(r'class="([^"]+)"', tag)
            if cls_match:
                cls = cls_match.group(1)
                if "inner" in cls and inner_idx is None:
                    inner_idx = idx
                if "special" in cls and special_idx is None:
                    special_idx = idx
            idx += 1
        depth += 1
        close_pos = block_content.find("</div>", pos)
        if close_pos == -1:
            break
        pos = close_pos + 6
        depth -= 1

    idx = special_idx if special_idx is not None else inner_idx
    if idx is not None and idx >= 2:
        idx -= 2  # Le serveur exclut 2 divs wrapper
    return idx


def solve_quiz():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; QuizSolver/1.0)"})

    # 1. Récupérer la page
    resp = session.get(BASE_URL)
    html = resp.text

    # 2. Extraire le quiz_id du formulaire
    quiz_id_match = re.search(
        r'<input[^>]*value="([a-f0-9-]{36})"[^>]*hidden[^>]*name="quiz_id"',
        html,
    )
    quiz_id = quiz_id_match.group(1) if quiz_id_match else ""

    # 3. Compter les paires de balises div (chaque <div> = 1 paire)
    div_count = len(re.findall(r"<div", html, re.I))

    # 4. Trouver le bloc caché et le div "special" parmi les enfants directs
    block_content = extract_hidden_block(html)
    special_index = find_special_div_index(block_content) if block_content else None

    # 5. Soumettre les réponses
    submit_url = "https://ctf.2600.eu/admissions/web_quizz/submit"
    data = {
        "div_count": div_count,
        "special_div_index": special_index,
        "quiz_id": quiz_id,
    }

    post_resp = session.post(submit_url, data=data)
    return post_resp.text


def solve_quiz_selenium():
    """Version Selenium - utilise le DOM réel du navigateur (plus fiable)."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        print("Selenium non installé. Utilisez: pip install selenium", file=sys.stderr)
        sys.exit(1)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(BASE_URL)

        quiz_id = driver.find_element("css selector", 'input[name="quiz_id"]').get_attribute("value")
        div_count = len(driver.find_elements("tag name", "div"))

        hidden = driver.find_element("css selector", 'div[style*="display: none"]')
        children = hidden.find_elements("xpath", "./div")
        inner_idx = special_idx = None
        for idx, child in enumerate(children):
            cls = child.get_attribute("class") or ""
            if "inner" in cls and inner_idx is None:
                inner_idx = idx
            if "special" in cls and special_idx is None:
                special_idx = idx
        special_index = special_idx if special_idx is not None else inner_idx

        driver.find_element("id", "div_count").send_keys(str(div_count))
        driver.find_element("id", "special_div_index").send_keys(str(special_index))
        driver.find_element("css selector", 'input[type="submit"]').click()

        return driver.page_source
    finally:
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--selenium", action="store_true", help="Utiliser Selenium (Chrome)")
    args = parser.parse_args()

    if args.selenium:
        result = solve_quiz_selenium()
    else:
        result = solve_quiz()
    print(result)
