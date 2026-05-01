# Tracking System

Drakonya Nightmare Music Lab starts with simple CSV trackers before adding a database or dashboard.

## Trackers

- trackers/costs.csv
- trackers/tracks.csv
- trackers/batches.csv
- trackers/releases.csv
- trackers/analytics.csv
- trackers/slop_bin.csv

## Rule

Every generated track should eventually have a row in tracks.csv.

Every paid tool or subscription should have a row in costs.csv.

Every rejected track should have a row in slop_bin.csv if it might be reused, studied, or mocked by Electro Slop.

## Starting Costs

Current known project costs:

- Suno Pro: $10/month
- DistroKid Musician Plus: about $44/year

## Future Dashboard

The future dashboard should read from these trackers or from a SQLite database created from these tracker fields.
