import io
import json
import datetime
import oci
import os
import base64
from datetime import timedelta, timezone
 
def handler(ctx, data: io.BytesIO = None):
    # try:
    # Load request body
    headers = ctx.Headers()

    if "x-api-key" not in headers:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing x-api-key in headers"})
        }
    input_x_api_key = headers.get("x-api-key")
    if isinstance(input_x_api_key, list):
        input_x_api_key = input_x_api_key[0]
    print(f'Input is {input_x_api_key}')

    signer = oci.auth.signers.get_resource_principals_signer()
    # Initialize signer from resource principal
    secret_client = oci.secrets.SecretsClient(config = {},signer=signer)
    object_storage = oci.object_storage.ObjectStorageClient(config={}, signer=signer)

    # Validate x-api-key
    expected_x_api_key_OCID =  os.getenv("x-api-key-ocid") 
    expected_x_api_key_bundle = secret_client.get_secret_bundle(expected_x_api_key_OCID).data
    expected_x_api_key = base64.b64decode(expected_x_api_key_bundle.secret_bundle_content.content).decode("utf-8")
    

    if input_x_api_key != expected_x_api_key:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Unauthorized"})
        }

    # Setup parameters
    namespace = object_storage.get_namespace().data
    bucket_name = os.getenv("bucket_name")   # 🔁 Replace with your bucket name

    # Create PAR details
    details = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
        name=f"par-{datetime.datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        access_type="AnyObjectWrite",
        time_expires=datetime.datetime.now(timezone.utc) + timedelta(hours=1),
        bucket_listing_action="Deny",
    )

    # Generate PAR
    response = object_storage.create_preauthenticated_request(namespace, bucket_name, details)
    par_uri = response.data.access_uri

    return f"https://objectstorage.{signer.region}.oraclecloud.com{par_uri}"
 
    # except Exception as e:
        # return {
            # "statusCode": 500,
            # "body": json.dumps({"error": str(e)})
        # }