import json
import jwt
from datetime import datetime, timedelta, timezone
from src.framework.adapters.input.rest.response_formatter_utils import (
    ResponseFormatterUtils,
)
from src.framework.adapters.output.persistence.documentdb.documentdb import (
    DocumentDBAdapter,
)

from src.application.utils.encrypt_utils import EncryptUtils
from src.application.utils.request_utils import RequestUtils
from src.application.utils.oauth_constants import OAuthConstants
from src.application.utils.token_constants import TokenConstants


class SigninUseCase:

    def __init__(self, secret: str, mongo_client: DocumentDBAdapter):
        self.mongo_client = mongo_client
        self.secret = secret

    def process(self, event: dict):
        
        body_json = json.loads(event["body"])
        username = body_json["username"]
        password = body_json["password"]
        password_hex = EncryptUtils.encrypt(password)

        path = event["requestContext"]["path"]
        domain_name = event["requestContext"]["domainName"]

        query = {"username": username, "password": password_hex}
        user = self.mongo_client.read(query)

        if user is None:
            return ResponseFormatterUtils.get_response_message(
                {
                    "error": OAuthConstants.INVALID_CREDENTIALS_ERROR,
                    "error_description": OAuthConstants.INVALID_CREDENTIALS_ERROR_DESCRIPTION,
                },
                RequestUtils.HTTP_NOT_FOUND,
            )

        iat = datetime.now(tz=timezone.utc)
        exp = iat + timedelta(seconds=TokenConstants.DURATION)
        payload = {
            TokenConstants.CLAIM_ISS: "https://{}{}".format(domain_name, path),
            TokenConstants.CLAIM_SID: str(user["_id"]),
            TokenConstants.CLAIM_TYPE: TokenConstants.CLAIM_TOKEN_TYPE,
            TokenConstants.CLAIM_EXP: exp,
            TokenConstants.CLAIM_IAT: iat,
        }
        encoded_jwt = jwt.encode(
            payload, self.secret, algorithm=TokenConstants.ALG_ENCODE
        )

        return ResponseFormatterUtils.get_response_message(
            {
                "access_token": encoded_jwt,
                "token_type": TokenConstants.CLAIM_TOKEN_TYPE,
                "expires_in": TokenConstants.DURATION,
            },
            RequestUtils.HTTP_OK,
        )
