from quart import Quart, make_response
from bs4 import BeautifulSoup
import httpx

app = Quart('xmltv-mutator')

URL = 'http://xmltv.net/xml_files/{name}.xml'
VERSION = open('VERSION').read().strip()


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
    def _inner(programme):
        programme.append(BeautifulSoup().new_tag(element))
    return _inner


def remove_element(element):
    def _inner(programme):
        programme.find(element).extract()
    return _inner


def replace_element(element, with_):
    def _inner(programme):
        programme.find(element).replace_with(BeautifulSoup().new_tag(with_))
    return _inner


def not_sbs(programme):
    return programme['channel'][0] != '3'


_mutations = [
    (
        [none_of('previously-shown', 'premiere', 'new'), not_sbs],
        add_element('premiere')
    ),
    (
        all_of('previously-shown', 'premiere'),
        replace_element('premiere', 'repeat')
    )
]


@app.route('/<name>.xml')
async def guide(name: str):
    data = await mutate_guide(URL.format(name=name))
    return await make_response(data)


async def mutate_guide(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

        soup = BeautifulSoup(response.text, 'xml')

        for prg in soup.findAll('programme'):
            for matches, apply_ in _mutations:
                if isinstance(matches, (list, tuple)):
                    if all(m(prg) for m in matches):
                        apply_(prg)
                elif matches(prg):
                    apply_(prg)

        return str(soup)
        return soup.prettify()


if __name__ == "__main__":
    app.logger.warning(f'Running version {VERSION}')
    app.run('0.0.0.0')
