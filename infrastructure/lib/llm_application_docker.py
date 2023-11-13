import os
from constructs import Construct

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from aws_cdk import (
    aws_ecr as ecr,
    aws_ecr_assets as ecr_assets,
)


import cdk_ecr_deployment as ecrdeploy

class LLMApplicationDockerInfra(Construct):
    """
    Create a llm docker for ec2 to launch
    """
    @property
    def image_uri(self):
        return self._image_uri

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id)

        # ECR asset for our Docker image
        self.asset = ecr_assets.DockerImageAsset(
            self, "llm_smart_search", directory="./docker"
        )

        repo = ecr.Repository(
            self, 
            "ECR",
            repository_name="llm_smart_search",
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        self._image_uri = f'{repo.repository_uri}:latest'

        ecrdeploy.ECRDeployment(self, "DeployDockerImage1",
            src=ecrdeploy.DockerImageName(self.asset.image_uri),
            dest=ecrdeploy.DockerImageName(self._image_uri)
        )

        print(f'LLM image {self._image_uri} uploaded!')

        cdk.CfnOutput(
            self, f"LLMAppDockerImage", value=self._image_uri)
        


