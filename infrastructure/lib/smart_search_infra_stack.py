#!/usr/bin/env python3

import os

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from aws_cdk import (
    App, CfnOutput, Stack
)
from constructs import Construct


from lib.knowledge_vectordb_infra import KnowledgeVectorDbInfra
from lib.embedding_model_inference_infra import EmbeddingModelInferenceInfra
from lib.llm_application_docker import LLMApplicationDockerInfra
from lib.application_infra import ApplicationInfra


class SmartSearchInfraStack(Stack):
    def __init__(self, app: Construct, id: str, project_name:str, instance_type_em:str, **kwargs) -> None:
        super().__init__(app, id, **kwargs)

        self._opensearch_infra = KnowledgeVectorDbInfra(
            self,
            f'{project_name}KnowledgeVectorDb',
            **kwargs
        )

        self._em_inference_infra = EmbeddingModelInferenceInfra(
            self,
            f'{project_name}EmbeddingInference',
            project_name = project_name,
            instance_type = instance_type_em,
            **kwargs
        )

        llm_docker_image = LLMApplicationDockerInfra(
            self,
            f'{project_name}DockerImage',
            **kwargs
        )

        self._application_infra = ApplicationInfra(
            self,
            f'{project_name}Application',
            **kwargs
        )

    @property
    def opensearch_domain_endpoint(self):
        return self._opensearch_infra.domain_endpoint

    @property
    def em_endpoint_name(self):
        return self._em_inference_infra.endpoint_name

