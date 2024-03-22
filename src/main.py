import logging
import pymongo
from src.application.utils.environment import EnvironmentUtils
from src.application.utils.environment_constants import EnvironmentConstants
from src.framework.adapters.output.persistence.documentdb.documentdb import (
    DocumentDBAdapter,
)
from src.framework.adapters.input.rest.response_formatter_utils import (
    ResponseFormatterUtils,
)
from src.application.usecases.login.signin_use_case import SigninUseCase

logger = logging.getLogger()
logger.setLevel(logging.INFO)

mongo_uri = EnvironmentUtils.get_env(EnvironmentConstants.MONGO_URI.name)
database = EnvironmentUtils.get_env(EnvironmentConstants.DB_NAME.name)
database_client = pymongo.MongoClient(mongo_uri)
database_adapter = DocumentDBAdapter("users", database_client[database])

secret = EnvironmentUtils.get_env(EnvironmentConstants.SECRET.name)
signin_use_case = SigninUseCase(secret, database_adapter)

def lambda_handler(event, context):

    resource_path = event["requestContext"]["resourcePath"]
    http_method = event["requestContext"]["httpMethod"]

    if http_method == "POST" and resource_path == "/login":
        return signin_use_case.process(event)

    return ResponseFormatterUtils.get_response_message(
        {
            "error": "not_found",
            "error_description": "%s %s is not a valid resource." % (http_method, resource_path)
         }, 404
    )
