import os
from constructs import Construct

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from aws_cdk import (
    aws_iam as iam,
    aws_ecr_assets as ecr,
)


class LLMApplicationDockerInfra(Construct):
    @property
    def image_uri(self):
        return self.asset.image_uri

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id)

        region = os.environ.get("CDK_DEPLOY_REGION",
                                os.environ["CDK_DEFAULT_REGION"])
        account = os.environ.get("CDK_DEPLOY_ACCOUNT",
                                 os.environ["CDK_DEFAULT_ACCOUNT"])
        
        # ECR asset for our Docker image
        self.asset = ecr.DockerImageAsset(
            self, "llm_smart_search", directory="./docker"
        )

        image_uri = f'{account}.dkr.ecr.{region}.amazonaws.com:llm_smart_search:latest'
        print('image_uri: {image_uri}')
        self.asset.image_uri = image_uri

        cdk.CfnOutput(
            self, f"LLMAppDockerImage", value=self.image_uri)
        


