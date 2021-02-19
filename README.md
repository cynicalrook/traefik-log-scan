# Traefik Access Log Scanner

Traefik Access Log Scanner is a Python program that reads the Traefik Access Log and outputs
to a web page a bar chart and data table showing where external access attempts are coming from.

This was born out of a desire to satisfy my curiosity regarding just where all of these access
attempts were originating as well as a desire to learn more Python.  This is the result of my tinkering.

![alt text](https://github.com/cynicalrook/traefik-log-scan/blob/main/traefikscanlog.png?raw=true)

&nbsp;&nbsp;

## Requirements

You will need to configure your Traefik installation to:

1) Create an Access Log (this is not the default log)
2) Write the log in JSON format (default is Common Log Format)
3) Write the log to a location you can map a Docker volume to.

Documentation for this is here: <https://doc.traefik.io/traefik/observability/access-logs/>

&nbsp;&nbsp;

This uses the free IP lookup database from IP2LOCATION: <https://lite.ip2location.com/>.

Signup for a free account and copy your download token.  This program will automatically download
the right database if it doesn't exist and your token is in the config.ini.  

Current download size is about 12MB.  Fully extracted on disk is about 47MB.

&nbsp;&nbsp;

## Installation

This is intended to run in a Docker container, sample Docker Compose snippet:

```bash
  traefik-access-log:
    container_name: traefik-access-log
    image: traefik-access-log-scanner
    ports:
      - 8050:8050
    volumes:
      - $DOCKERDIR/traefik-scan:/app/data
      - $DOCKERDIR/shared:/app/log
    environment:
      - PUID=$PUID
      - PGID=$PGID
      - TZ=$TZ

```

On first run, the container will create a config.ini where you map '/app/data' and then terminates.
Edit your config.ini to include settings for your environment and start the container again.

```bash
[dev]
LOGFILE: logfile path and name
HOSTIP: 'dynamic' (without quotes) or enter host IP here
REFRESH INTERVAL: 10
IP2LOCATION TOKEN: token here
```

LOGFILE: full path and name of logfile, i.e. /app/log/traefikaccess.log

HOSTIP: dynamic or x.x.x.x.  Used to filter your external IP from the reporting.  The dynamic setting
assumes your installation is behind a NAT and that this container would have the same external address
as your Traefik server.  It will then determine the IP automatically, or you can directly specify the
IP address to exclude.

REFRESH INTERVAL: How often, in minutes, to grab new entries from the Traefik Access Log and update
the web page.

IP2LOCATION TOKEN: Get from the Account > File Download page of the IP2LOCATION Lite website after
you create your free account.

Once running, access the web page at <http://your_docker_IP:8050>  Note that you must have at least one
external connection attempt in the Traefik Access log or the process will fail and error out.  I know I should fix this,
but haven't gotten around to it yet...

## Contributing

This is just a hobby program, but if you want to enhance or modify, pull requests are welcome and I'd love to see what you have in mind!

Source code located here: <https://github.com/cynicalrook/traefik-log-scan>

For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
