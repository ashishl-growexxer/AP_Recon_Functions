import io
import json
import logging
import os
from fdk import response
import requests
import oci
import time
from oci.object_storage.models import CopyObjectDetails



def is_flask_app_alive(url: str) -> bool:
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            data = res.json()
            return data.get("status") == "alive"
        return False
    except Exception as e:
        print(f"Error checking Flask app: {e}")
        return False

def call_flask_api(file_path,flask_api_url):
    print(f"Inside flask api call")

    payload = {"file_path": file_path}
    print(f"flask api url: {flask_api_url}")
    
    try:
        resp = requests.post(flask_api_url, json=payload)
        resp.raise_for_status()
        return resp
    except requests.exceptions.RequestException as e:
        return {"error": "Failed to call Flask API", "details": str(e)}


def wait_for_copy_completion(client, work_request_id, max_retries=10):
        for attempt in range(1, max_retries + 1):
            work_request = client.get_work_request(work_request_id).data
            if work_request.status == 'COMPLETED':
                print("Copy completed successfully.")
                return True
            elif work_request.status == 'FAILED':
                raise Exception("Copy failed.")
            else:
                print("Copy in progress...")
                time.sleep(5)
        print("Too much time and data is not transferred.")
        return False



def handler(ctx, data: io.BytesIO = None):
    try:
        body = json.loads(data.getvalue())
        object_name = body["data"]["resourceName"]
        bucket_name = body["data"]["additionalDetails"]["bucketName"]
        namespace = body["data"]["additionalDetails"]["namespace"]

        file_path = f"oci://{bucket_name}@{namespace}/{object_name}"
        app_url = os.getenv("app_url")
        signer = oci.auth.signers.get_resource_principals_signer()
        healthcheck_url = app_url + "/process-healthcheck"

        if object_name.split('/')[0] == "New":
            if is_flask_app_alive(healthcheck_url):
                requests.get(app_url+"/polling_unprocessed")
                app_trigger_uri = app_url + "/get-file-content"
                res = call_flask_api(file_path = file_path,flask_api_url= app_trigger_uri)
                return response.Response(
                    ctx, response_data=json.dumps(
                        {"message": "VM on, sent api to handle request and got response"}),
                    headers={"Content-Type": "application/json"}
                )
            else:
                object_storage = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
                destination_path = "Unprocessed/" + object_name.split('/')[-1]
                copy_details = CopyObjectDetails(
                    source_object_name=object_name,
                    destination_bucket=bucket_name,
                    destination_namespace=namespace,
                    destination_object_name=destination_path,
                    destination_region="ap-mumbai-1"
                )
                res = object_storage.copy_object(
                    namespace_name=namespace,
                    bucket_name=bucket_name,
                    copy_object_details=copy_details
                )
                work_request_id = res.headers['opc-work-request-id']
                if not wait_for_copy_completion(object_storage, work_request_id):
                    return 0
                object_storage.delete_object(namespace_name=namespace,bucket_name=bucket_name,object_name=object_name)
                return response.Response(
                    ctx, response_data=json.dumps(
                        {"message": "VM Down, pushed to Unprocessed"}),
                    headers={"Content-Type": "application/json"}
                )
        else:
            return response.Response(
                ctx, response_data=json.dumps(
                    {"message": "Filepath not in New"}),
                headers={"Content-Type": "application/json"}
            )

    except (Exception, ValueError) as ex:
        logging.getLogger().info('error parsing json payload: ' + str(ex))
        return response.Response(
            ctx, response_data=json.dumps(
                {"message": "Failed Function"}),
            headers={"Content-Type": "application/json"}
        )


