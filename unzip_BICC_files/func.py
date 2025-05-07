import io
import json
import logging
import zipfile
import os
import oci
import io 

from fdk import response


def handler(ctx, data):
    logging.getLogger().info("Function invoked")
    signer = oci.auth.signers.get_resource_principals_signer()
    object_storage = oci.object_storage.ObjectStorageClient({}, signer=signer)
    namespace = os.getenv("NAMESPACE")
    bucket_name = os.getenv("BUCKET_NAME")
    endpoint_folder_path = os.getenv("UNZIPPED_FOLDER")

    if not namespace or not bucket_name:
        raise ValueError("Missing NAMESPACE or BUCKET_NAME in environment variables.")
    # Parse event payload
    event_data = json.loads(data.read().decode('utf-8'))
    zip_object_name = event_data['data']['resourceName']
    if not zip_object_name.lower().endswith('.zip') :
        if not zip_object_name.lower().endswith('.csv') :
            object_storage.delete_object(namespace, bucket_name, zip_object_name)
        return response.Response(ctx, status_code=200, response_data="Not a zip file.")

    logging.getLogger().info("before downloading zip")
    # Download zip
    zip_response = object_storage.get_object(namespace, bucket_name, zip_object_name)
    zip_content = zip_response.data.content
    # Extract and upload CSVs
    with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
        for name in zip_file.namelist():
            if name.lower().endswith('.csv'):
                csv_data = zip_file.read(name)
                dest_object_name = endpoint_folder_path + f'/{name}'
                object_storage.put_object(
                    namespace,
                    bucket_name,
                    dest_object_name,
                    csv_data
                )
                logging.info(f"Uploaded CSV: {dest_object_name}")
    logging.getLogger().info("zip file extracted ")
    # Delete original ZIP
    object_storage.delete_object(namespace, bucket_name, zip_object_name)
    logging.info(f"Deleted source ZIP: {zip_object_name}")
    list_objects_response = object_storage.list_objects(
	    namespace,
	    bucket_name,
	    prefix=endpoint_folder_path)
    
    return response.Response(ctx, status_code=200, response_data="CSV files extracted and uploaded.")

