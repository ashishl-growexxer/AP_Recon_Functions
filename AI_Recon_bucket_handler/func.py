import io
import json
import logging
import os 
import oci
import requests
from fdk import response

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


def handler(ctx, data: io.BytesIO = None):
    try:
        body = json.loads(data.getvalue())
        object_name = body["data"]["resourceName"]
        bucket_name = body["data"]["additionalDetails"]["bucketName"]
        namespace = body["data"]["additionalDetails"]["namespace"]

        file_path = f"oci://{bucket_name}@{namespace}/{object_name}"
        app_url = os.getenv("app_url")

        if object_name.split('/')[0] == "New":
            print(object_name.split('/')[1].split('_')[0])
            if object_name.split('/')[1].split('_')[0]=="AP":
                print(object_name.split('/')[1].split('_')[0])
                app_trigger_uri = app_url + "/get-file-content"
                res = call_flask_api(file_path = file_path,flask_api_url= app_trigger_uri)
                return response.Response(
                    ctx, response_data=json.dumps(
                        {"message": "VM on, sent api to handle request and got response"}),
                    headers={"Content-Type": "application/json"}
                )
            return response.Response(
                ctx, response_data=json.dumps(
                    {"message": "Reconciliation"}),
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




