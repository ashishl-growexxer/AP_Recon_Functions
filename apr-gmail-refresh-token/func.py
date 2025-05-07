import io
import json
import requests
import os 
import base64 
import oci

from fdk import response
 
def handler(ctx, data: io.BytesIO = None):

    signer = oci.auth.signers.get_resource_principals_signer()
    secret_client = oci.secrets.SecretsClient({}, signer=signer)
    # 👇 Your OAuth credentials
    client_id_ocid = os.getenv("CLIENT_ID_OCID")
    client_id_bundle = secret_client.get_secret_bundle(client_id_ocid).data
    client_id = base64.b64decode(client_id_bundle.secret_bundle_content.content).decode("utf-8")

    client_secret_ocid = os.getenv("CLIENT_SECRET_OCID")
    client_secret_bundle = secret_client.get_secret_bundle(client_secret_ocid).data
    client_secret = base64.b64decode(client_secret_bundle.secret_bundle_content.content).decode("utf-8")

    refresh_token_ocid = os.getenv("REFRESH_TOKEN_OCID")
    refresh_token_bundle = secret_client.get_secret_bundle(refresh_token_ocid).data
    refresh_token = base64.b64decode(refresh_token_bundle.secret_bundle_content.content).decode("utf-8")
 
    # 👇 Google OAuth 2.0 token endpoint
    token_url = "https://oauth2.googleapis.com/token"
 
    # 👇 Payload to get a new access token
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
 
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
 
    # 👇 Make a POST request to Google's OAuth server
    token_response = requests.post(token_url, data=payload, headers=headers)
 
    if token_response.status_code == 200:
        # 👇 Success
        token_json = token_response.json()
        access_token = token_json.get("access_token")
        access_token = "Bearer "+ access_token
        return response.Response(
            ctx,
            response_data=json.dumps({"access_token":access_token}),
            headers={"Content-Type": "application/json"}
        )
    else:
        # 👇 Error handling
        return response.Response(
            ctx,
            status_code=token_response.status_code,
            response_data=json.dumps({"error": "Failed to get access token", "details": token_response.text}),
            headers={"Content-Type": "application/json"}
        )