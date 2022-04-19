import asyncio
import datetime
from quart import Quart, make_response
from bs4 import BeautifulSoup
import httpx
import json

app = Quart('xmltv-mutator')

URL = 'http://xmltv.net/xml_files/{name}.xml'
VERSION = open('VERSION').read().strip()
JSON_DATA = '_imdb_movie_year_cache.json'

try:
    _imdb_movie_year_cache = json.load(open(JSON_DATA))
except OSError:
    _imdb_movie_year_cache = {}


def none_of(*elements):
    def _inner(programme):
        return not any(
            programme.find(element)
            for element in elements
        )
    return _inner


def all_of(*elements):
    def _inner(programme):
        return all(programme.find(element) for element in elements)
    return _inner


def add_element(element):
    async def _inner(programme, session=None):
        programme.append(BeautifulSoup().new_tag(element))
    return _inner


def remove_element(element):
    async def _inner(programme, session=None):
        programme.find(element).extract()
    return _inner


def replace_element(element, with_):
    async def _inner(programme, session=None):
        programme.find(element).replace_with(BeautifulSoup().new_tag(with_))
    return _inner


def not_sbs(programme):
    return programme['channel'][0] != '3'


def movie(programme):
    return any(
        'movie' in category.text.lower()
        for category in programme.find_all('category')
    )


async def get_movie_year(url, session=None):
    if 'tttt' in url:
        url = url.replace('tttt', 'tt')
    if url not in _imdb_movie_year_cache:
        print(f'Fetching year for {url}')
        response = await session.get(
            f'https://imdb.com/{url}/releaseinfo?ref_=tt_ov_rdat'
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        date = soup.find('td', class_='release-date-item__date')
        if not date:
            import pdb; pdb.set_trace()
        try:
            _imdb_movie_year_cache[url] = str(
                datetime.datetime.strptime(date.text, '%d %B %Y').date()
            )
        except ValueError:
            _imdb_movie_year_cache[url] = date.text.strip()
    return _imdb_movie_year_cache[url]


async def force_movie(programme, session=None):
    element = BeautifulSoup().new_tag('category')
    element.append('Movie')
    programme.append(element)
    if programme.find('episode-num', system="imdb.com"):
        year = BeautifulSoup().new_tag('date')
        year.append(await get_movie_year(
            programme.find('episode-num', system="imdb.com").text,
            session=session,
        ))
        programme.append(year)


_mutations = [
    (
        [none_of('previously-shown', 'premiere', 'new'), not_sbs],
        add_element('premiere')
    ),
    (
        all_of('previously-shown', 'premiere'),
        replace_element('premiere', 'repeat')
    ),
    (movie, force_movie),
]


@app.route('/<name>.xml')
async def guide(name: str):
    data = await mutate_guide(URL.format(name=name))
    return await make_response(data)


async def mutate_guide(url: str) -> str:
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    session = httpx.AsyncClient(limits=limits)
    response = await session.get(url)
    soup = BeautifulSoup(response.text, 'xml')
    await asyncio.gather(*[
        apply_(prg, session=session)
        for matches, apply_ in _mutations
        for prg in soup.find_all('programme')
        if (
            all(m(prg) for m in matches)
            if isinstance(matches, (list, tuple))
            else matches(prg)
        )
    ])
    await session.aclose()
    json.dump(_imdb_movie_year_cache, open(JSON_DATA, 'w'), indent=2)

    # for prg in soup.findAll('programme'):
    #     for matches, apply_ in _mutations:
    #         if isinstance(matches, (list, tuple)):
    #             if all(m(prg) for m in matches):
    #                 apply_(prg)
    #         elif matches(prg):
    #             apply_(prg)

    return str(soup)


if __name__ == "__main__":
    app.logger.warning(f'Running version {VERSION}')
    app.run('0.0.0.0')
