# xmltv-mutator
Mutate XMLTV guide data to fix errors.

When using [Channels](https://getchannels.com) with the [XMLTV data for Australia](http://xmltv.net/), I found there were a bunch of things that were just not quite right.

For instance, episodes on the ABC that did not have the `<previously-shown>` tag did not have the `<premiere>` tag; this caused Channels to not mark these episodes as "New".

This is problematic because these episodes are often repeated several times during the week, resulting in no way to filter these out.

This is an attempt to fix that. It runs a [Quart](https://pypi.org/project/quart/) server that acts as a proxy, downloading the referenced file, mutating it, and then returning the mutated version.

## Mutations

The following mutations are applied to each program:

  * If the program does not contain `<previously-shown>`, then add the `<premiere>` tag (if it is not present). This excludes SBS programmes, which do not contain the `<previously-shown>` element.
  * If the program contains both `<previously-shown>` and `<premiere>` tags, remove the latter.

## Running the server

You can run the server locally, to debug issues or add extra mutations:

    $ poetry install
    $ poetry shell
    $ python app.py

 It listens on interface 0.0.0.0 to enable you to point your Channels (or other DVR) at this server.

 You'll probably want to run it in a better way: I run Channels DVR using a `docker-compose.yml` file, which can be extended to run this server too:

    version: "3.5"

    networks:
      lan:
        external: true
        name: net_lan

    services:
      channels-dvr:
        image: fancybits/channels-dvr:latest
        container_name: channels-dvr
        depends_on:
          - xmltv-mutator
        networks:
          lan:
            ipv4_address: 10.1.101.100
        ports:
          - "80:8089"
        restart: always
        devices:
          - /dev/dri:/dev/dri
        volumes:
          - /mnt/disk/dvr/config:/channels-dvr
          - /mnt/disk/dvr/recordings:/shares/DVR
      xmltv-mutator:
        image: schinckel/xmltv-mutator:0.1.3
        restart: always
        container_name: xmltv-mutator
        networks:
          lan:
            ipv4_address: 10.1.101.101

Your setup may vary. I use an external network, for instance.
