import io
import logging
import oci
from fdk import response
from urllib.parse import urlparse, parse_qs

# Configure logging level
logging.basicConfig(level=logging.INFO)

def handler(ctx, data: io.BytesIO = None):
    try:
        logging.info("Function execution started.")
        logging.info("This function starts and stops OIC")
        parsed_url = urlparse(ctx.RequestURL())
        query_params = parse_qs(parsed_url.query)
        is_start = query_params.get("to_start", [None])[0]

        cfg = ctx.Config()

        integration_instance_id = cfg.get("INTEGRATION_INSTANCE_ID")
        logging.info(f"Retrieved integration instance ID: {integration_instance_id}")

        if not integration_instance_id:
            raise ValueError("INTEGRATION_INSTANCE_ID not provided in function config.")

        # Use resource principal signer
        logging.info("Initializing resource principal signer.")
        signer = oci.auth.signers.get_resource_principals_signer()

        # Create Integration client
        logging.info("Creating IntegrationInstanceClient.")
        integration_client = oci.integration.IntegrationInstanceClient(config={}, signer=signer)

        if is_start=='0':
            logging.info("Stopping OIC instance.")
            stop_response = integration_client.stop_integration_instance(
                integration_instance_id=integration_instance_id
            )
            logging.info(f"Stop request submitted. Status: {stop_response.status}")
            if 'opc-request-id' in stop_response.headers:
                logging.info(f"OPC Request ID: {stop_response.headers['opc-request-id']}")

            return response.Response(
                ctx,
                response_data=f"Stop request submitted: {stop_response.status}",
                status_code=200
            )
        elif is_start=='1':
            logging.info("Starting OIC instance.")
            start_repsonse = integration_client.start_integration_instance(
                integration_instance_id=integration_instance_id
            )
            logging.info(f"Start request submitted. Status: {start_repsonse.status}")
            return response.Response(
                ctx,
                response_data=f"Start request submitted: {start_repsonse.status}",
                status_code=200
            )
        else:
            logging.info("Starting OAC instance.")
            return response.Response(
                ctx,
                response_data=f"Unknown request on OAC url submitted , please only give 1 to start or 0 to stop",
                status_code=200
            )        

    except Exception as e:
        logging.error("Error occurred while stopping integration instance.", exc_info=True)
        return response.Response(
            ctx,
            response_data=f"Internal Server Error: {str(e)}",
            status_code=500
        )
