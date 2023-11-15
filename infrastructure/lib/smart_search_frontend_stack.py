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
from lib.frontend_infra import FrontEndInfra


class SmartSearchFrontendStack(Stack):
    def __init__(self, app: Construct, id: str, project_name:str, semantic_search_api:str, summarize_api:str, **kwargs) -> None:
        super().__init__(app, id, **kwargs)

        front_end_infra = FrontEndInfra(
            self,
            f"{project_name}Frontend",
            main_api=semantic_search_api,
            summarize_api=summarize_api,
            **kwargs,
        )

