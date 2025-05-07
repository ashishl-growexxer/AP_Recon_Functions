
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
from urllib.parse import urlparse, parse_qs


processed_requests = {}


async def handler(ctx, data: io.BytesIO = None):
    logger = logging.getLogger()
    logger.info('parsing Request data payload: ')
    parsed_url = urlparse(ctx.RequestURL())
    query_params = parse_qs(parsed_url.query)
    vendor_name = query_params.get("vendor_name", [None])[0]

    logger.info(f'vendor_name: {vendor_name}')

    result = await trigger(logger=logger,vendor =vendor_name)

    return response.Response(
        ctx, status_code=200,
        response_data=json.dumps({"message": "Vendor data deleted"})
    )


async def trigger(logger,vendor):
    logger.info(f'reached trigger function with vendor {vendor}')
    signer = oci.auth.signers.get_resource_principals_signer()
    secret_client = oci.secrets.SecretsClient({}, signer=signer)

    user_secret_id = os.getenv('user_ocid')
    pass_secret_id = os.getenv('password_ocid')

    # Fetch secret bundles
    user_bundle = secret_client.get_secret_bundle(user_secret_id).data
    pass_bundle = secret_client.get_secret_bundle(pass_secret_id).data

    # Decode Base64-encoded content
    username = base64.b64decode(user_bundle.secret_bundle_content.content).decode("utf-8")
    password = base64.b64decode(pass_bundle.secret_bundle_content.content).decode("utf-8")


    # API endpoint
    url = os.getenv('oci_url')
    logger.info(f"We have recived trigger request and collected details") 

    if not vendor:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing 'vendor_name' in query string"})
        }
    payload = {"vendor_name": vendor}
    auth_string = f"{username}:{password}"
    basic_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    headers = {"Content-Type": "application/json","Authorization": f"Basic {basic_auth}"}


    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response Body: {response.text}")
        except Exception as e:
            logger.error(f"Error calling webhook: {str(e)}")
        

    return 'OK', 200

	

    
