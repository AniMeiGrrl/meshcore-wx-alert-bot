# Finding NWS county codes

The NWS Alerts API filters counties using Universal Geographic Code identifiers
in the form:

```text
SSCNNN
```

- `SS` is the two-letter state abbreviation.
- `C` means county.
- `NNN` is the county portion of the UGC.

Examples:

```text
MIC081  Kent County, Michigan
TXC201  Harris County, Texas
CAC037  Los Angeles County, California
```

These are not ZIP codes, and they should not be guessed from a FIPS code
without verifying them against NWS data.

## Built-in lookup

After installing the project:

```sh
meshcore-wxbot list-counties MI \
  --user-agent "meshcore-wxbot/1.0 (operator@example.com)"
```

Or from the deployed virtual environment:

```sh
/opt/meshcore-wxbot/venv/bin/meshcore-wxbot \
  list-counties TX \
  --user-agent "meshcore-wxbot/1.0 (operator@example.com)"
```

Copy the desired codes and names into `config.yaml`:

```yaml
nws:
  counties:
    - {code: TXC201, name: Harris}
```

## Official API lookup

The NWS county-zone endpoint can also be queried directly:

```text
https://api.weather.gov/zones/county?area=MI
```

Send an identifying User-Agent when using scripts. The response contains
GeoJSON features with an `id` and county `name`.

The active-alert endpoint for one county is:

```text
https://api.weather.gov/alerts/active?zone=MIC081
```

Official references:

- [NWS API documentation](https://www.weather.gov/documentation/services-web-api)
- [NWS alerts documentation](https://www.weather.gov/documentation/services-web-alerts)
- [NWS Alerts Geolocation Guide](https://www.weather.gov/media/documentation/docs/NWS_Geolocation.pdf)

## County versus forecast zone

NWS county UGCs use `C`; public forecast zones commonly use `Z`. This project’s
configuration validator intentionally expects county codes. If a warning covers
several configured counties, the API may return the same NWS alert through
multiple county queries. The bot merges those results by alert identifier.
