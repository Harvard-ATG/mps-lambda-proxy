from flask_lambda import FlaskLambda
from flask import request
import requests
import logging

app = FlaskLambda(__name__)
app.logger.setLevel(logging.INFO)

@app.route("/ingest", methods=["POST"])
def ingest_proxy():
    VALID_ENDPOINTS=[
        "https://mps-admin-dev.lib.harvard.edu/admin/ingest/initialize",
        "https://mps-admin-qa.lib.harvard.edu/admin/ingest/initialize",
        "https://mps-admin-prod.lib.harvard.edu/admin/ingest/initialize"
    ]
    app.logger.info("Proxy server received ingest request")
    data = request.json
    payload = data.get("req")
    endpoint = data.get("endpoint")
    token = request.headers.get("Authorization")

    if(endpoint not in VALID_ENDPOINTS):
        app.logger.info(f"Invalid endpoint {endpoint}")
        return(f"Invalid endpoint {endpoint}", 422)
    app.logger.info(f"Proxying ingest request for {endpoint} from {request.remote_addr}")
    app.logger.info(payload)

    r = requests.post(endpoint, headers={"Authorization": token}, json=payload)
    app.logger.info("Response from MPS")
    app.logger.info(r.json())
    return(r.content, r.status_code, r.headers.items())


@app.route("/jobstatus", methods=["GET"])
def jobstatus_proxy():
    VALID_ENDPOINTS=[
        "https://mps-admin-dev.lib.harvard.edu/admin/ingest/jobstatus",
        "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus",
        "https://mps-admin-prod.lib.harvard.edu/admin/ingest/jobstatus"
    ]
    app.logger.info("Proxy server received job status request")
    try:
        url = request.args.get("job_url")
        valid_endpoint = url.startswith(tuple(VALID_ENDPOINTS))
        if valid_endpoint:
            r = requests.get(url)
            app.logger.info(r.json())
            return(r.content, r.status_code, r.headers.items())
        else:
            raise Exception("Job status endpoint invalid")
    except Exception as e:
        app.logger.error("Job status URL not found or invalid")
        app.logger.error(e)
        return(f"Error. Did you provide a valid job_url URL parameter?", 403)


if __name__ == "__main__":
    app.run(debug=True)