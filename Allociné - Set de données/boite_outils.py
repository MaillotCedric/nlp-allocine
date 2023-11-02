import requests
from bs4 import BeautifulSoup

def get_nombre_pages(url):
    requete = requests.get(url)
    soupe = BeautifulSoup(requete.text, "html.parser")
    pagination = soupe.find(
        "div",
        {
            "class": "pagination-item-holder"
        }
    )
    liens_pages = pagination.find_all("span")
    nombre_pages = int([lien.text for lien in liens_pages][-1])

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
