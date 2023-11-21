import os
import json

from constructs import Construct
import aws_cdk as cdk

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_secretsmanager as sm,
    aws_iam as iam,
    CfnOutput,
)


class SemanticSearchLambdaStack(Stack):
    def __init__(
        self,
        app: Construct,
        construct_id: str,
        search_engine: str,
        em_endpoint_name: str,
        **kwargs,
    ) -> None:
        super().__init__(app, construct_id, **kwargs)

        host_url_secret = sm.Secret(
            self,
            "OpenSearchHostURLSecret",
            generate_secret_string=sm.SecretStringGenerator(
                secret_string_template=json.dumps({"host": search_engine}),
                generate_string_key="urlkey",
            ),
            secret_name="OpenSearchHostURL",
        )

        # create lambda for semantic search
        semantic_lambda = self._create_semantic_lambda(
            id=construct_id, host=search_engine, em_endpoint_name=em_endpoint_name
        )

        # create an api gateway for this lambda
        self._create_apigw(region=kwargs["env"].region, semantic_lambda=semantic_lambda)

    def _create_semantic_lambda(self, id, host, em_endpoint_name):
        index = self.node.try_get_context("semantic_search_index_name")

        # configure the lambda role
        _role_policy = iam.PolicyStatement(
            actions=[
                "sagemaker:InvokeEndpointAsync",
                "sagemaker:InvokeEndpoint",
                "lambda:AWSLambdaBasicExecutionRole",
                "secretsmanager:SecretsManagerReadWrite",
                "es:ESHttpPost",
            ],
            resources=["*"],
        )

        semantic_search_role = iam.Role(
            self,
            "semantic_search_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        semantic_search_role.add_to_policy(_role_policy)

        semantic_search_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        semantic_search_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite")
        )

        # add langchain processor for smart query and answer
        function_name = "semantic_search"
        semantic_lambda = _lambda.Function(
            self,
            id,
            function_name=function_name,
            runtime=_lambda.Runtime.PYTHON_3_9,
            role=semantic_search_role,
            code=_lambda.Code.from_asset(
                "../lambda/" + function_name,
                bundling=cdk.BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_9.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt --no-cache-dir -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            handler="semantic_search" + ".lambda_handler",
            memory_size=256,
            timeout=Duration.minutes(5),
        )

        semantic_lambda.add_environment("host", host)
        semantic_lambda.add_environment("index", index)
        semantic_lambda.add_environment("embedding_endpoint_name", em_endpoint_name)

        return semantic_lambda

    def _create_apigw(self, region, semantic_lambda):
        # api gateway resource
        self._api = apigw.RestApi(
            self,
            "semantic-search-api",
            endpoint_types=[apigw.EndpointType.REGIONAL],
        )

        semantic_lambda_root = self._api.root.add_resource(
            "smart_search",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_methods=["POST", "OPTIONS"],
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_credentials=True,
                allow_headers=[
                    "Content-Type",
                    "X-Amz-Date",
                    "Authorization",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                ],
            ),
        )

        semantic_lambda_api_integration = apigw.LambdaIntegration(
            semantic_lambda,
            proxy=True,
            integration_responses=[
                apigw.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": "'*'"
                    },
                )
            ],
        )

        semantic_lambda_root.add_method(
            "POST",
            semantic_lambda_api_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    },
                )
            ],
        )

        CfnOutput(
            self,
            "SemanticSearchApi",
            export_name="SemanticSearchApi",
            value=f"https://{self._api.rest_api_id}.execute-api.{region}.amazonaws.com/prod",
        )
