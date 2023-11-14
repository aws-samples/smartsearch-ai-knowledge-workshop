import os
import typing
from constructs import Construct

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import  aws_cloudfront_origins as origins
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

        # prepare the static web pages
        self._prepare_static_web_pages(main_api, summarize_api)

        # create website bucket
        website_bucket = self._create_and_upload_asset_to_s3(id)

        # Create cloudfront
        distribution = self._create_cloudfront_distribution(website_bucket)
        self._grant_cloudfront_access(distribution, website_bucket)

        cdk.CfnOutput(
            self,
            "SmartSearchUrl",
            value=f'https://{distribution.distribution_domain_name}',
            description="Smart search url",
        )
    
    def _prepare_static_web_pages(self, main_api, summarize_api):
        build_static_web_cmd = f"""export REACT_APP_MAIN_API={main_api} |
        				export REACT_APP_SUMMARIZE_API={summarize_api} |
						./build-s3-dist.sh
                """
        os.system(build_static_web_cmd)

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
            sources=[s3_deployment.Source.asset(os.path.join(DIRNAME, "../../front-end/build"))],
            destination_bucket=website_bucket
        )
        return website_bucket

    def _create_cloudfront_distribution(self, website_bucket):
        distribution:cloudfront.CloudFrontWebDistribution = cloudfront.CloudFrontWebDistribution(
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
                            allowed_methods=cloudfront.CloudFrontAllowedMethods.ALL,
                            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
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

        overriden_distribution = typing.cast(
            cloudfront.CfnDistribution,
            distribution.node.default_child,
        )

        overriden_distribution.add_property_override(
            'DistributionConfig.Origins.0.OriginAccessControlId',
            cfn_origin_access_control.get_att('Id'),
        )
        
        return distribution

    def _grant_cloudfront_access(self, distribution, website_bucket):
        # add cloudfront access policy
        website_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject"],
                resources=[f"{website_bucket.bucket_arn}/*"],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                # principals=[iam.ArnPrincipal(f"arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity {distribution.distribution_id}")],
                sid="PolicyForCloudFrontPrivateContent",
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{os.environ['CDK_DEFAULT_ACCOUNT']}:distribution/{distribution.distribution_id}"
                    }
                },
            )
        )