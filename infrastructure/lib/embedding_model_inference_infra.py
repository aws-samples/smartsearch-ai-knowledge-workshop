import os
from constructs import Construct

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_cloudwatch as cloudwatch,
    aws_sagemaker as sagemaker,
    aws_applicationautoscaling as asg,
)

from .config import PYTORCH_VERSION, TRANSFORMERS_VERSION, PY_VERSION, REGION_DICT


class EmbeddingModelInferenceInfra(Construct):

    @property
    def endpoint_name(self):
        return self._endpoint_name

    @property
    def endpoint_ref(self):
        return self._endpoint_ref

    def __init__(self, scope: Construct, id: str, project_name:str, instance_type:str, **kwargs):
        super().__init__(scope, id)

        # env info
        self._region = kwargs['env'].region
        self._instance_type = instance_type
        self._project_name = project_name

        # partition
        self._deploy_partition = "aws"
        if self._region.startswith("cn"):
            self._deploy_partition = "aws-cn"

        self._sagemaker_role = self._create_sagemaker_role()

        endpoint = self._create_endpoint()

        self._endpoint_name = endpoint.attr_endpoint_name
        self._endpoint_ref = endpoint.ref

        cdk.CfnOutput(
            self, f"SageMakerEndpoint", value=self._endpoint_name)

    def _create_endpoint(self):
        instance_type = self._instance_type

        image_uri = self._get_sagemaker_image_uri()

        # ===========================
        # ===== SAGEMAKER MODEL =====
        # ===========================
        model = sagemaker.CfnModel(
            self,
            f"Model",
            execution_role_arn=self._sagemaker_role.role_arn,
            # the properties below are optional
            enable_network_isolation=False,
            containers=[
                sagemaker.CfnModel.ContainerDefinitionProperty(
                    container_hostname=f"{self._project_name}ContainerHostname",
                    image=image_uri,
                    mode="SingleModel",
                    environment={
                        "HF_TASK": "feature-extraction",
                        "HF_MODEL_ID": "shibing624/text2vec-base-chinese",
                        "SAGEMAKER_CONTAINER_LOG_LEVEL": 20,
                        "SAGEMAKER_REGION": cdk.Aws.REGION,
                    },
                )
            ],
        )

        # model.node.add_dependency(self._model_deployment)

        # =====================================
        # ===== SAGEMAKER ENDPOINT CONFIG =====
        # =====================================
        variant_name = "AllTraffic"
        endpoint_config = sagemaker.CfnEndpointConfig(
            self,
            f"EPConfig",
            production_variants=[
                sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                    initial_instance_count=1,
                    initial_variant_weight=1.0,
                    instance_type=instance_type,
                    model_name=model.attr_model_name,
                    variant_name=variant_name,
                )
            ],
        )

        endpoint_config.add_dependency(model)
        # endpoint_config.add_depends_on(model)
        # ==============================
        # ===== SAGEMAKER ENDPOINT =====
        # ==============================

        endpoint = sagemaker.CfnEndpoint(
            self,
            f"{self._project_name}Endpoint",
            endpoint_name=f'{self._project_name}Endpoint',
            endpoint_config_name=endpoint_config.attr_endpoint_config_name,
        )
        cdk.CfnOutput(
            self, "SagemakerModelEndpoint", value=endpoint.attr_endpoint_name
        )

        # add the autoscaling policy
        target = asg.ScalableTarget(
            self,
            "ScalableTarget",
            service_namespace=asg.ServiceNamespace.SAGEMAKER,
            max_capacity=2,
            min_capacity=1,
            resource_id=f"endpoint/{endpoint.attr_endpoint_name}/variant/{variant_name}",
            scalable_dimension="sagemaker:variant:DesiredInstanceCount",
            role=self._sagemaker_role
        )
        target.node.add_dependency(endpoint)

        target.scale_to_track_metric(
            "GPU35Tracking",
            target_value=35,
            custom_metric=cloudwatch.Metric(
                metric_name="GPUUtilization",
                namespace="/aws/sagemaker/Endpoints",
                period=cdk.Duration.minutes(3),
                dimensions_map={
                    "EndpointName": endpoint.attr_endpoint_name,
                    "VariantName": variant_name,
                },
                statistic="Average",
            ),
            scale_in_cooldown=cdk.Duration.seconds(600),
            scale_out_cooldown=cdk.Duration.seconds(300),
        )

        return endpoint

    def _create_sagemaker_role(self):
        # IAM Roles
        name = "Sagemaker"
        sagemaker_role = iam.Role(
            self,
            f"{name}Role",
            description="SageMaker role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy(
                    self,
                    f"{name}Policy",
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                # "s3:DeleteObject",
                                "s3:GetBucketAcl",
                                "s3:PutObjectAcl",
                                "s3:AbortMultipartUpload",
                            ],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::*SageMaker*",
                                f"arn:{self._deploy_partition}:s3:::*Sagemaker*",
                                f"arn:{self._deploy_partition}:s3:::*sagemaker*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:GetObject"],
                            resources=["*"],
                            conditions={
                                "StringEqualsIgnoreCase": {
                                    "s3:ExistingObjectTag/SageMaker": "true"
                                }
                            },
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["iam:PassRole"],
                            resources=["*"],
                            conditions={
                                "StringEquals": {
                                    "iam:PassedToService": "sagemaker.amazonaws.com"
                                }
                            },
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:GetBucketAcl", "s3:PutObjectAcl"],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::*SageMaker*",
                                f"arn:{self._deploy_partition}:s3:::*Sagemaker*",
                                f"arn:{self._deploy_partition}:s3:::*sagemaker*",
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*sagemaker*",
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*SageMaker*",
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*Sagemaker*",
                                f"arn:{self._deploy_partition}:lambda:*:*:function:*LabelingFunction*",
                            ],
                        ),
                        iam.PolicyStatement(
                            actions=["s3:ListBucket"],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::sagemaker*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        iam.PolicyStatement(
                            actions=["s3:CreateBucket"],
                            resources=[
                                f"arn:{self._deploy_partition}:s3:::*SageMaker*",
                                f"arn:{self._deploy_partition}:s3:::*Sagemaker*",
                                f"arn:{self._deploy_partition}:s3:::*sagemaker*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "sagemaker:DescribeEndpointConfig",
                                "sagemaker:DescribeModel",
                                "sagemaker:InvokeEndpoint",
                                "sagemaker:ListTags",
                                "sagemaker:DescribeEndpoint",
                                "sagemaker:CreateModel",
                                "sagemaker:CreateEndpointConfig",
                                "sagemaker:CreateEndpoint",
                                "sagemaker:DeleteModel",
                                "sagemaker:DeleteEndpointConfig",
                                "sagemaker:DeleteEndpoint",
                                "sagemaker:CreateTrainingJob",
                                "sagemaker:DescribeTrainingJob",
                                "sagemaker:UpdateEndpoint",
                                "sagemaker:UpdateEndpointWeightsAndCapacities",
                                "autoscaling:*",
                                "ecr:GetAuthorizationToken",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:BatchCheckLayerAvailability",
                                # "ecr:SetRepositoryPolicy",
                                # "ecr:CompleteLayerUpload",
                                # "ecr:BatchDeleteImage",
                                # "ecr:UploadLayerPart",
                                # "ecr:DeleteRepositoryPolicy",
                                # "ecr:InitiateLayerUpload",
                                # "ecr:DeleteRepository",
                                # "ecr:PutImage",
                                # "ecr:CreateRepository",
                                # "ec2:CreateVpcEndpoint",
                                # "ec2:DescribeRouteTables",
                                "cloudwatch:PutMetricData",
                                "cloudwatch:GetMetricData",
                                "cloudwatch:GetMetricStatistics",
                                "cloudwatch:ListMetrics",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:GetLogEvents",
                                "logs:CreateLogGroup",
                                "logs:DescribeLogStreams",
                                "iam:ListRoles",
                                "iam:GetRole",
                            ],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["kms:Decrypt",
                                     "kms:Encrypt", "kms:CreateGrant"],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["iam:CreateServiceLinkedRole"],
                            resources=[
                                "arn:aws:iam::*:role/aws-service-role/sagemaker.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_SageMakerEndpoint"
                            ],
                            conditions={
                                "StringLike": {
                                    "iam:AWSServiceName": "sagemaker.application-autoscaling.amazonaws.com",
                                }
                            },
                        ),
                    ],
                )
            ],
        )

        cdk.CfnOutput(self, "SagemakerRoleName", value=sagemaker_role.role_name)

        return sagemaker_role

    def _get_sagemaker_image_uri(self):
        repository = (
            f"{REGION_DICT[self._region]}.dkr.ecr.{self._region}.amazonaws.com/huggingface-pytorch-inference"
        )
    
        tag = f"{PYTORCH_VERSION}-transformers{TRANSFORMERS_VERSION}-{'gpu-py39-cu117' if self._is_gpu_instance() else 'cpu-py39'}-ubuntu20.04"
        return f"{repository}:{tag}"

    def _is_gpu_instance(self):
        return True if self._instance_type.split(".")[1][0].lower() in ["p", "g"] else False

