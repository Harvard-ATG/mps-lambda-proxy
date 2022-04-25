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
    logging.info(context)
    path = event.get("rawPath").lstrip("/").rstrip("/")
    logging.info(path)
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
    logging.info(body)
    content_type = event["headers"]["content-type"]
    logging.info(content_type)
    body_decoded = base64.b64decode(body)
    logging.info(body_decoded)
    
    # data = json.loads(event.get("body", None))
    # payload = data.get("req")
    body = json.loads(body_decoded)
    token = body.get("token")
    payload = body.get("payload")
    endpoint = INGEST_ENDPOINTS.get(lts_env) 
    # token = event.get("headers").get("Authorization")
    sourceIp = event.get("headers").get("x-forwarded-for")

    logging.info(f"Proxying ingest request for {endpoint} from {sourceIp}")
    logging.info(payload)
    logging.info(token)

    r = requests.post(endpoint, headers={"Authorization": token}, json=payload)  # type: ignore
    res = {
        "statusCode": r.status_code,
        "headers": dict(r.headers.items()),
        "body": r.json()
    }
    logging.info("Response from MPS")
    logging.info(res)
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
        logging.info(f"Getting {url}")
        r = requests.get(url)
        logging.info(r)
        logging.info(r.status_code)
        logging.info(r.reason)
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