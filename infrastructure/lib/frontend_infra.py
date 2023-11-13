import os
from constructs import Construct

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from aws_cdk import aws_cloudfront as cloudfront
import aws_cdk.aws_iam as iam

DIRNAME = os.path.dirname(__file__)

class FrontEndInfra(Construct):
    """
    Create front end infra with s3 to hold static web page.
    Cloudfront to be accessed in front of s3.
    """
    def __init__(
        self, scope: Construct, id: str, main_api: str, summarize_api: str, **kwargs
    ):
        super().__init__(scope, id)
        print(f'search api: {main_api}, summarize api: {summarize_api}')

        self._prepare_static_web_pages(main_api, summarize_api)

        website_bucket = self._create_and_upload_asset_to_s3(id)

        # Create cloudfront
        distribution = self._create_cloudfront_distribution(website_bucket)

        # s3_client = boto3.client("s3")
        # local_directory = "../front-end/build"
        # # 遍历本地目录并上传文件
        # for root, dirs, files in os.walk(local_directory):
        #     for file in files:
        #         local_file_path = os.path.join(root, file)
        #         s3_key = os.path.relpath(local_file_path, local_directory)
        #         print("s3_key", s3_key)
        #         try:
        #             # 执行文件上传
        #             s3_client.upload_file(local_file_path, s3_bucket_name, s3_key)
        #             print(f"Uploaded {local_file_path} to {s3_bucket_name}/{s3_key}")
        #         except Exception as e:
        #             print(f"Error uploading {local_file_path}: {str(e)}")

        self._grant_cloudfront_access(distribution, kwargs, website_bucket)

        cdk.CfnOutput(
            self,
            "SmartSearchUrl",
            value=f'https://{distribution.distribution_domain_name}/search',
            description="Smart search url",
        )

    def _grant_cloudfront_access(self, distribution, kwargs, website_bucket):
        # add cloudfront access policy
        website_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject"],
                resources=[f"{website_bucket.bucket_arn}/*"],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                sid="PolicyForCloudFrontPrivateContent",
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{kwargs['env'].account}:distribution/{distribution.distribution_id}"
                    }
                },
            )
        )

    def _create_cloudfront_distribution(self, website_bucket):
        distribution = cloudfront.CloudFrontWebDistribution(
            self,
            "StaticWebsiteDistribution",
            origin_configs=[
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=website_bucket,
                        origin_access_identity=None,
                    ),
                    behaviors=[
                        cloudfront.Behavior(
                            is_default_behavior=True,
                            compress=True,
                            allowed_methods=cloudfront.CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
                        )
                    ],
                ),
            ],
            default_root_object="index.html"
        )

        
        # add access control for frontend
        cfn_origin_access_control = cloudfront.CfnOriginAccessControl(
            self,
            id="StaticWebsiteDistributionControl",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="StaticWebsiteDistributionControlConfig",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4",
                description="Default Origin Access Control",
            ),
        )
        return distribution

    def _create_and_upload_asset_to_s3(self, prefix):
        # create a bucket to host static content
        s3_bucket_name = "smart-search-static-website-bucket"
        website_bucket = s3.Bucket(
            self,
            id=f'{prefix}StaticWebsiteBucket',
            bucket_name=s3_bucket_name,
            website_index_document="index.html",
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True,
            ),
        )

        # deploy to s3 website_bucket
        models_deployment = s3_deployment.BucketDeployment(
            self,
            "Models",
            sources=[s3_deployment.Source.asset(os.path.join(DIRNAME, "../front-end/build"))],
            destination_bucket=website_bucket,
            destination_key_prefix="search"
        )
        return website_bucket

    def _prepare_static_web_pages(self, main_api, summarize_api):
        build_static_web_cmd = f"""export REACT_APP_MAIN_API={main_api}
        				export REACT_APP_SUMMARIZE_API={summarize_api}
						./build-s3-dist.sh
                """
        os.system(build_static_web_cmd)
