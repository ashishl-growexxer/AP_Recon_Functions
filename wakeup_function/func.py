import io
import json
import logging
import asyncio
import uuid
from fdk import response
import oci
import requests
from flask import Flask,request
from requests.auth import HTTPBasicAuth


# In-memory store for processed idempotency keys (for demo purposes only)
# In production, use a persistent storage solution.
processed_requests = {}

async def handler(ctx, data: io.BytesIO = None):
    # Attempt to extract an idempotency key from the request payload.
    # If not provided, you can generate one (though it's better if the caller provides one).
    try:
        body = json.loads(data.getvalue())
    except Exception as ex:
        logging.getLogger().info('Error parsing JSON payload: ' + str(ex))
        body = {}

    idempotency_key = body.get("idempotency_key", None)
    if not idempotency_key:
        # Optionally generate a new key, but ideally the client should send one.
        idempotency_key = str(uuid.uuid4())
        logging.getLogger().info("Generated idempotency key: " + idempotency_key)
    
    # Check if the request has already been processed.
    if processed_requests.get(idempotency_key):
        logging.getLogger().info("Duplicate execution detected for key: " + idempotency_key)
        return response.Response(ctx, status_code=200,
                                 response_data=json.dumps({"message": "Duplicate execution ignored.", 
                                                             "idempotency_key": idempotency_key}))
    
    # Mark the idempotency key as processed.
    processed_requests[idempotency_key] = True

    # Proceed with your normal function logic.
    logging.getLogger().info("Inside Python Hello World function with key: " + idempotency_key)
    # Run the wakeup async function and wait for completion.
    result = await wakeup(ctx)
    return result

async def wakeup(ctx):
    logging.getLogger().info("Wakeup function called")
    signer = oci.auth.signers.get_resource_principals_signer()  # Uses resource principal authentication
    logging.getLogger().info(f"Got signer: {signer}")
    
    fnmgmt = oci.functions.FunctionsManagementClient({}, signer=signer)
    logging.getLogger().info("Created FunctionsManagementClient")
    
    fnapp_id = "ocid1.fnapp.oc1.ap-mumbai-1.aaaaaaaaro25mmihnnl6pq6iyt4nldydiwxuswobqa2vbthzy5lmpr2afgfq"
    fns = fnmgmt.list_functions(fnapp_id)
    # Retrieved function list
    
    fnlist = fns.data  # List of FunctionSummary objects
    # Invoking functions from list by creating invokationclient and using it 
    
    # Create a client to invoke functions using the invoke endpoint of the first function.
    fninvoke = oci.functions.FunctionsInvokeClient({}, service_endpoint=fnlist[0].invoke_endpoint, signer=signer,timeout=90)
    logging.getLogger().info("Created FunctionsInvokeClient for invoking function")
    
    # Invoke each function concurrently in a detached mode.
    await asyncio.gather(*(asyncio.to_thread(fninvoke.invoke_function, fn.id, fn_invoke_type='detached') for fn in fnlist ))
    
    return response.Response(ctx, status_code=204)
