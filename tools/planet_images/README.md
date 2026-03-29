

This folder contains scripts to generate planet imagery for the game. This imagery is hosted centrally and is not part of the deployed game assets.

We need to upload this CORS policy to the bucket to allow it to be accessed from any origin:
```
gcloud storage buckets update gs://openstars-assets \
  --cors-file=cors-any-origin.json
```