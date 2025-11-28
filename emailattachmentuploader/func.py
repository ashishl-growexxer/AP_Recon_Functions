import io
import json
import logging

from fdk import response


def handler(ctx, data: io.BytesIO = None):
    request = ctx.Request()
    validation_token = request.params.get("validationToken")
    
    if validation_token:
        return response.Response(
            ctx,
            response_data=validation_token,
            headers={"Content-Type": "text/plain"},
            status_code=200
        )
    
    # Handle notifications after subscription is validated
    return response.Response(
        ctx,
        response_data="OK",
        status_code=200
    )