import requests
import logging
import json
import base64

if logging.getLogger().hasHandlers():
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

def lambda_handler(event: dict, context: object) -> dict:
    # "/<environment>/<action>" eg /prod/ingest
    logging.info(event)
    path = event.get("rawPath").lstrip("/").rstrip("/")
    ENVIRONMENTS = ["dev", "qa", "prod"]
    if "jobstatus" in path:
        lts_env, action, job_id = path.split("/")
    else:
        lts_env, action = path.split("/")
    if(lts_env not in ENVIRONMENTS):
        msg = f"Invalid environment {lts_env}"
        logging.error(msg)
        return {
            "body": msg,
            "statusCode": 403
        }

    if action == "initialize":
        return ingest(event, lts_env=lts_env)
    elif action == "jobstatus":
        return jobstatus(event, lts_env=lts_env, job_id=job_id)
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
    
    body = event.get("body")
    body_decoded = base64.b64decode(body)
    data = json.loads(body_decoded)

    token = data.get("token")
    payload = data.get("payload")
    endpoint = INGEST_ENDPOINTS.get(lts_env) 
    # token = event.get("headers").get("Authorization") # this no longer works, auth headers are overwritten by AWS signing request
    sourceIp = event.get("headers").get("x-forwarded-for")

    logging.info(f"Proxying ingest request for {endpoint} from {sourceIp}")

    r = requests.post(endpoint, headers={"Authorization": token}, json=payload)  # type: ignore
    res = {
        "statusCode": r.status_code,
        "headers": dict(r.headers.items()),
        "body": r.json()
    }
    return res

def jobstatus(event, lts_env: str, job_id: str):
    ENDPOINTS = {
        "dev": "https://mps-admin-dev.lib.harvard.edu/admin/ingest/jobstatus",
        "qa": "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus",
        "prod": "https://mps-admin-prod.lib.harvard.edu/admin/ingest/jobstatus"
    }
    logging.info(f"Proxy server received job status request from {lts_env} for job_id {job_id}")
    try:
        endpoint = ENDPOINTS.get(lts_env)
        url = f"{endpoint}/{job_id}"
        r = requests.get(url)
        res = {
            "statusCode": r.status_code,
            "headers": dict(r.headers.items()),
            "body": r.json()
        }
        logging.info(res)
        return res
    except Exception as e:
        msg = "Job ID param or endpoint not found or invalid. Is job_id valid?"
        logging.error(msg)
        logging.error(e)
        return {
            "body": msg,
            "statusCode": 403
        }