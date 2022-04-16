import requests
import logging
import json

if logging.getLogger().hasHandlers():
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context) -> dict:
    path = event.get("rawPath")
    # "/<environment>/<action>" eg /prod/ingest
    ENVIRONMENTS = ["dev", "qa", "prod"]
    lts_env, action = path.lstrip("/").split("/")
    if(lts_env not in ENVIRONMENTS):
        msg = f"Invalid environment {lts_env}"
        logging.error(msg)
        return {
            "body": msg,
            "statusCode": 403
        }

    if action == "ingest":
        return ingest(event, lts_env=lts_env)
    elif action == "jobstatus":
        return jobstatus(event, lts_env=lts_env)
    else:
        msg = f"Error, invalid endpoint {path}"
        logging.critical(msg)
        return {
            "body": msg,
            "statusCode": 403
        }

def ingest(event, lts_env: str):
    INGEST_ENDPOINTS={
        "dev": "https://mps-admin-dev.lib.harvard.edu/admin/ingest/initialize",
        "qa": "https://mps-admin-qa.lib.harvard.edu/admin/ingest/initialize",
        "prod": "https://mps-admin-prod.lib.harvard.edu/admin/ingest/initialize"
    }

    logging.info(f"Proxy server received ingest request for env {lts_env}")
    data = json.loads(event.get("body", None))
    payload = data.get("req")
    endpoint = INGEST_ENDPOINTS.get(lts_env) 
    token = event.get("headers").get("Authorization")
    sourceIp = event.get("headers").get("x-forwarded-for")

    logging.info(f"Proxying ingest request for {endpoint} from {sourceIp}")
    logging.info(payload)

    r = requests.post(endpoint, headers={"Authorization": token}, json=payload)  # type: ignore
    logging.info("Response from MPS")
    logging.info(r.json())
    return {
        "statusCode": r.status_code,
        "headers": r.headers.items(),
        "body": r.json()
    }

def jobstatus(event, lts_env: str):
    ENDPOINTS = {
        "dev": "https://mps-admin-dev.lib.harvard.edu/admin/ingest/jobstatus",
        "qa": "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus",
        "prod": "https://mps-admin-prod.lib.harvard.edu/admin/ingest/jobstatus"
    }
    logging.info(f"Proxy server received job status request from f{lts_env}")
    try:
        job_id = event.get("queryStringParameters").get("job_id")
        endpoint = ENDPOINTS.get(lts_env)
        url = f"{endpoint}/{job_id}"
        r = requests.get(url)
        logging.info(r.json())
        res = {
            "statusCode": r.status_code,
            "headers": dict(r.headers.items()),
            "body": r.json()
        }
        return res
    except Exception as e:
        msg = "Job ID param or endpoint not found or invalid. Is job_id valid?"
        logging.error(msg)
        logging.error(e)
        return {
            "body": msg,
            "statusCode": 403
        }