# mps-iiif-lambda-proxy
A Lambda to proxy request for the MPS Admin URLs through a Cloudwatch enabled VPC for whitelisting

## Install

## Deploy
- `poetry build`
- `poetry run pip install -t package dist/*.whl`
- `cp mps_iiif_lambda_proxy/proxy.py package/lambda_function.py ; cd package ; zip -r ../artifact.zip . -x '*.pyc'`