import requests
import re
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from collections import defaultdict

def get_nombre_pages(url):
    requete = requests.get(url)
    soupe = BeautifulSoup(requete.text, "html.parser")
    pagination = soupe.find(
        "div",
        {
            "class": "pagination-item-holder"
        }
    )

    if pagination:
        tout_index_pages_visibles = len(pagination.find_all("span")) == 1

        if tout_index_pages_visibles:
            liens_pages = pagination.find_all("a")
        else:
            liens_pages = pagination.find_all("span")

        nombre_pages = int([lien.text for lien in liens_pages][-1])
    else:
        nombre_pages = 0

    return nombre_pages

def get_urls_page(url_page):
    requete = requests.get(url_page)
    soupe = BeautifulSoup(requete.text, "html.parser")
    liens_fiche_film = soupe.find_all(
        "a",
        {
            "class": "meta-title-link"
        }
    )

    return [lien.get("href") for lien in liens_fiche_film]

def get_urls_films(url_site, nombre_maximal_pages=None):
    urls_films = []
    url_tous_films = f"{url_site}/films"
    limite = nombre_maximal_pages if nombre_maximal_pages else get_nombre_pages(url_tous_films)

    for index_page in range(0, limite):
        url_page = f"{url_tous_films}/?page={index_page}"
        urls_films_page = get_urls_page(url_page)
        urls_films.extend(urls_films_page)

    return urls_films

def get_id_film(url):
    return re.findall(r'\d+', url)[0]

def erreur_navigation(requete):
    url_non_trouvee = requete.status_code == requests.codes.not_found # url is not found : film does not exist
    # if there is more than two element in history, the request was redirected
    # and that means there are no "critiques/spectateurs" page
    redirection = len(requete.history) > 2

    if url_non_trouvee or redirection:
        return True
    else:
        return False

def get_note(balise_html_note):
    span_note = balise_html_note.find("span", {"class": "stareval-note"}) # <span class="stareval-note">4,0</span>
    note_str = str(span_note.contents)[2:5]  # "4,0"
    note = float(note_str.replace(',', '.'))  # 4.0

    return note

def format_text(comment):
    output_text = ""

    for content in comment.contents:
        content_str = str(content)
        content_soup = BeautifulSoup(content_str, 'html.parser')
        spoiler = content_soup.find("span", {"class": "spoiler-content"})
        if spoiler:
            output_text += spoiler.text.strip()
        else:
            output_text += content_str.strip()

    return output_text

def get_elements_critiques_page(url_page_commentaires):
    commentaires, notes = [], []
    requete = requests.get(url_page_commentaires)
    soupe = BeautifulSoup(requete.text, "html.parser")
    balises_html_notes = soupe.find_all("div", {"class": "review-card-review-holder"})
    balises_html_commentaires = soupe.find_all("div", attrs={"class": "content-txt review-card-content"})

    for balise_html_commentaire in balises_html_commentaires:
        commentaire = format_text(balise_html_commentaire)

        commentaires.append(commentaire)

    for balise_html_note in balises_html_notes:
        note = get_note(balise_html_note)

        notes.append(note)

    return commentaires, notes

def get_elements_critiques(url_critiques_film, nombre_maximal_pages_commentaires):
    commentaires, notes = [], []
    requete = requests.get(url_critiques_film)

    if erreur_navigation(requete):
        return None

    soupe = BeautifulSoup(requete.text, "html.parser")
    limite = nombre_maximal_pages_commentaires if nombre_maximal_pages_commentaires else get_nombre_pages(url_critiques_film)

    for index_page in range(1, limite + 1):
        url_page_commentaires = f"{url_critiques_film}/?page={index_page}"
        commentaires, notes = get_elements_critiques_page(url_page_commentaires)

    return (commentaires, notes)

def get_commentaires(url_site, urls, nombre_maximal_pages_commentaires=None):
    dict_allocine = defaultdict(list)

    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

    for i, url in enumerate(urls):
        id_film = get_id_film(url)
        url_critiques_film = f"{url_site}/film/fichefilm-{id_film}/critiques/spectateurs"
        elements_critiques = get_elements_critiques(url_critiques_film, nombre_maximal_pages_commentaires)

        if elements_critiques:
            commentaires, notes = elements_critiques

            # Rarely happens
            if not(len(commentaires) == len(notes)):
                continue

            dict_allocine['commentaire'].extend(commentaires)
            dict_allocine['note'].extend(notes)

    return dict_allocine
