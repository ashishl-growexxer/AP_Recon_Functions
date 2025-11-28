import logging
from fdk import response
import io
import json
import oci
from datetime import datetime, timezone, timedelta
import time
from email.utils import parsedate_to_datetime

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
        # Load configuration from the default location
        signer = oci.auth.signers.get_resource_principals_signer()
        object_storage = oci.object_storage.ObjectStorageClient({}, signer=signer)

        # Set your namespace, bucket, and paths
        namespace = object_storage.get_namespace().data
        bucket_name = "AIR-Data-bucket"
        source_prefix = "Processed/"
        destination_prefix = "Archived/Processed"
        
        # Time threshold
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)

        # List objects with prefix
        objects = object_storage.list_objects(namespace, bucket_name, prefix=source_prefix).data.objects

        for obj in objects:

            object_name = obj.name
            head_response = object_storage.head_object(namespace,bucket_name,object_name)
            logging.getLogger().info(f"Header Response :{head_response}")
            last_modified_str = head_response.headers.get('last-modified')
            if not last_modified_str:
                continue
            last_modified = parsedate_to_datetime(last_modified_str)


            if last_modified < one_day_ago:
                logging.getLogger().info(f"Moving {object_name} last modified at {last_modified}")

                # Extract just the filename part
                filename = object_name[len(source_prefix):]
                new_object_name = destination_prefix + filename

                # Copy object
                copy_request = oci.object_storage.models.CopyObjectDetails(
                    source_object_name=object_name,
                    destination_bucket=bucket_name,
                    destination_namespace=namespace,
                    destination_object_name=new_object_name,
                    destination_region="ap-mumbai-1"
                )
                response = object_storage.copy_object(namespace, bucket_name, copy_object_details=copy_request)
                work_request_id = response.headers['opc-work-request-id']
                if not wait_for_copy_completion(object_storage, work_request_id):
                    return "Move failed"

                # Delete original object
                object_storage.delete_object(namespace, bucket_name, object_name)

        return "Move completed"

    except Exception as e:
        logging.getLogger().info(f"Error: {str(e)}")
        raise
