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
        logging.info("This function starts and stops OAC")
        parsed_url = urlparse(ctx.RequestURL())
        query_params = parse_qs(parsed_url.query)
        is_start = query_params.get("to_start", [None])[0]
        cfg = ctx.Config()

        analytics_instance_id = cfg.get("OAC_INSTANCE_ID")
        logging.info(f"Retrieved OAC instance ID: {analytics_instance_id}")

        if not analytics_instance_id:
            raise ValueError("OAC_INSTANCE_ID not provided in function config.")

        # Use resource principal signer
        logging.info("Initializing resource principal signer.")
        signer = oci.auth.signers.get_resource_principals_signer()

        # Create Analytics client
        logging.info("Creating AnalyticsClient.")
        analytics_client = oci.analytics.AnalyticsClient(config={}, signer=signer)

        # Send stop request
        logging.info(f"Sending stop request for OAC instance: {analytics_instance_id}")
        if is_start=='0':
            logging.info("Stopping OAC instance.")
            stop_response = analytics_client.stop_analytics_instance(
                analytics_instance_id=analytics_instance_id
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
            logging.info("Starting OAC instance.")
            start_repsonse = analytics_client.start_analytics_instance(
                analytics_instance_id=analytics_instance_id
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
        logging.error("Error occurred while stopping OAC instance.", exc_info=True)
        return response.Response(
            ctx,
            response_data=f"Internal Server Error: {str(e)}",
            status_code=500
        )
