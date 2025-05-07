import io
import json
import logging
import uuid
from fdk import response
import requests
from requests.auth import HTTPBasicAuth
import httpx
import os 
import base64
import oci


# In-memory store for processed idempotency keys (for demo purposes only)
# In production, use a persistent storage solution.
processed_requests = {}


async def handler(ctx, data: io.BytesIO = None):
    logger = logging.getLogger()
    try:
        body = json.loads(data.getvalue())
    except Exception as ex:
        logger.info('Error parsing JSON payload: ' + str(ex))
        body = {}

    idempotency_key = body.get("idempotency_key", None)
    if not idempotency_key:
        # Optionally generate a new key, but ideally the client should send one.
        idempotency_key = str(uuid.uuid4())
        logger.info("Generated idempotency key: " + idempotency_key)
    
    # Check if the request has already been processed.
    if processed_requests.get(idempotency_key):
        logger.info("Duplicate execution detected for key: " + idempotency_key)
        return response.Response(ctx, status_code=200,response_data=json.dumps({"message": "Duplicate execution ignored.", "idempotency_key": idempotency_key}))
    
    # Mark the idempotency key as processed.
    processed_requests[idempotency_key] = True

    # Proceed with your normal function logic.
    logger.info("Inside Python Hello World function with key: " + idempotency_key)
    # Run the wakeup async function and wait for completion.
    result = await trigger(ctx,body,logger)
    return response.Response(
        ctx, status_code=200,
        response_data=json.dumps({"message": "Webhook triggered", "idempotency_key": body.get("idempotency_key")})
    )


async def trigger(ctx,body,logger):
    signer = oci.auth.signers.get_resource_principals_signer()
    secret_client = oci.secrets.SecretsClient({}, signer=signer)

    user_secret_id = os.getenv("USER_SECRET_OCID")
    pass_secret_id = os.getenv("PASS_SECRET_OCID")

    # Fetch secret bundles
    user_bundle = secret_client.get_secret_bundle(user_secret_id).data
    pass_bundle = secret_client.get_secret_bundle(pass_secret_id).data

    # Decode Base64-encoded content
    username = base64.b64decode(user_bundle.secret_bundle_content.content).decode("utf-8")
    password = base64.b64decode(pass_bundle.secret_bundle_content.content).decode("utf-8")


    # API endpoint
    url = os.getenv("url")
    logger.info(f"We have recived trigger request and collected details .Base on authetication details , Based on given credentials we need to provide right steps") 
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=body, auth=(username, password))
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response Body: {response.text}")
        except Exception as e:
            logger.error(f"Error calling webhook: {str(e)}")
        

    return 'OK', 200

	

    
