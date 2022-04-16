import requests
import logging
import json

if logging.getLogger().hasHandlers():
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):
    print(event)
    print(context)
    path = event.get("rawPath")
    print(path)
    if path == "/ingest":
        return ingest(event)
    elif path == "/jobstatus":
        return jobstatus(event)
    else:
        msg = "Error, invalid endpoint"
        logging.critical(msg)
        return(msg)

def ingest(event):
    VALID_ENDPOINTS=[
        "https://mps-admin-dev.lib.harvard.edu/admin/ingest/initialize",
        "https://mps-admin-qa.lib.harvard.edu/admin/ingest/initialize",
        "https://mps-admin-prod.lib.harvard.edu/admin/ingest/initialize"
    ]
    logging.info("Proxy server received ingest request")
    data = json.loads(event.get("body", None))
    payload = data.get("req")
    endpoint = data.get("endpoint") 
    token = event.get("headers").get("Authorization")
    sourceIp = event.get("headers").get("x-forwarded-for")

    if(endpoint not in VALID_ENDPOINTS):
        logging.error(f"Invalid endpoint {endpoint}")
        return(f"Invalid endpoint {endpoint}", 422)
    logging.info(f"Proxying ingest request for {endpoint} from {sourceIp}")
    logging.info(payload)

    r = requests.post(endpoint, headers={"Authorization": token}, json=payload)
    logging.info("Response from MPS")
    logging.info(r.json())
    return {
        "statusCode": r.status_code,
        "headers": r.headers.items(),
        "body": r.json()
    }

def jobstatus(event):
    VALID_ENDPOINTS=[
        "https://mps-admin-dev.lib.harvard.edu/admin/ingest/jobstatus",
        "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus",
        "https://mps-admin-prod.lib.harvard.edu/admin/ingest/jobstatus"
    ]
    logging.info("Proxy server received job status request")
    print("Proxy server received job status request")
    try:
        url = event.get("queryStringParameters").get("job_url")
        print(url)
        valid_endpoint = url.startswith(tuple(VALID_ENDPOINTS))
        print(valid_endpoint)
        if valid_endpoint:
            r = requests.get(url)
            logging.info(r.json())
            print(r.json())
            print(r.headers.items())
            print(dict(r.headers.items()))
            res = {
                "statusCode": r.status_code,
                "headers": dict(r.headers.items()),
                "body": r.json()
            }
            print(res)
            print(json.dumps(res))
            return res
        else:
            msg = "Job status endpoint invalid"
            logging.error(msg)
            return(msg)
    except Exception as e:
        logging.error("Job status URL not found or invalid")
        logging.error(e)
        return {
            "body": "Error. Did you provide a valid job_url URL parameter?",
            "statusCode": 403
        }