import pulumi
import pulumi_aws as aws


class Module(pulumi.ComponentResource):
    def __init__(
        self, module_name: str, opts: pulumi.ResourceOptions | None = None
    ) -> None:
        super().__init__("wenke:module:about", module_name, opts=opts)


class LandingPageModule(Module):
    def __init__(
        self,
        module_name: str = "landing-page",
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(module_name, opts)

        config = pulumi.Config("aws")
        tags = config.require_object("defaultTags")["tags"]

        bucket = aws.s3.BucketV2(
            f"{tags['project']}-{module_name}-{tags['stack']}",
            opts=pulumi.ResourceOptions(parent=self),
        )

        log_bucket = aws.s3.BucketV2(
            f"{tags['project']}-{module_name}-{tags['stack']}-logs",
            opts=pulumi.ResourceOptions(parent=self),
        )

        virginia = aws.Provider(
            f"{tags['project']}-{module_name}-{tags['stack']}",
            region="us-east-1",
            opts=pulumi.ResourceOptions(parent=self),
        )
        certificate = aws.acm.Certificate(
            f"{tags['project']}-{module_name}-{tags['stack']}",
            domain_name="*.wenke-studio.com",
            validation_method="DNS",
            opts=pulumi.ResourceOptions(parent=self, provider=virginia),
        )
        validation = certificate.domain_validation_options[0]

        zone = aws.route53.get_zone(name="wenke-studio.com")
        aws.route53.Record(
            f"{tags['project']}-{module_name}-{tags['stack']}",
            zone_id=zone.id,
            name=validation.resource_record_name,
            type=validation.resource_record_type,
            ttl=300,
            records=[validation.resource_record_value],
        )

        cache_policy = aws.cloudfront.get_cache_policy(name="Managed-CachingOptimized")
        response_header_policy = aws.cloudfront.get_response_headers_policy(
            name="Managed-SecurityHeadersPolicy"
        )
        origin_access_control = aws.cloudfront.OriginAccessControl(
            f"{tags['project']}-{module_name}-{tags['stack']}",
            origin_access_control_origin_type="s3",
            signing_behavior="always",
            signing_protocol="sigv4",
            opts=pulumi.ResourceOptions(parent=self),
        )
        distribution = aws.cloudfront.Distribution(
            f"{tags['project']}-{module_name}-{tags['stack']}",
            # Settings
            enabled=True,
            comment="about.wenke-studio.com",  # Description
            aliases=["about.wenke-studio.com"],  # CNAME
            default_root_object="index.html",
            http_version="http1.1",
            is_ipv6_enabled=True,
            price_class="PriceClass_100",
            viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
                acm_certificate_arn=certificate.arn,
                ssl_support_method="sni-only",
                minimum_protocol_version="TLSv1.2_2021",
            ),
            # Origin
            origins=[
                aws.cloudfront.DistributionOriginArgs(
                    domain_name=bucket.bucket_regional_domain_name,
                    origin_id=bucket.id,
                    origin_access_control_id=origin_access_control.id,
                    # custom_headers=
                )
            ],
            # Behavior
            default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
                allowed_methods=["GET", "HEAD"],
                cached_methods=["GET", "HEAD"],
                viewer_protocol_policy="redirect-to-https",
                compress=True,
                target_origin_id=bucket.id,
                cache_policy_id=cache_policy.id,
                # origin_request_policy_id=
                response_headers_policy_id=response_header_policy.id,
            ),
            # Error (for SPA)
            custom_error_responses=[
                aws.cloudfront.DistributionCustomErrorResponseArgs(
                    error_code=404,
                    response_code=200,
                    response_page_path="/index.html",
                ),
            ],
            # GEO
            restrictions=aws.cloudfront.DistributionRestrictionsArgs(
                geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
                    restriction_type="none",
                )
            ),
            # Logger
            # logging_config=aws.cloudfront.DistributionLoggingConfigArgs(
            #     bucket=log_bucket.id,
            #     include_cookies=True,
            #     prefix="about/",
            # ),
            opts=pulumi.ResourceOptions(parent=self),
        )

        aws.route53.Record(
            f"{tags['project']}-{module_name}-{tags['stack']}-about",
            zone_id=zone.id,
            name=distribution.comment,  # distribution.aliases[0]
            type="CNAME",
            ttl=300,
            records=[distribution.domain_name],
        )

        document = aws.iam.get_policy_document(
            version="2008-10-17",
            policy_id="PolicyForCloudFrontPrivateContent",
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    sid="AllowCloudFrontServicePrincipal",
                    effect="Allow",
                    principals=[
                        aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                            type="Service",
                            identifiers=["cloudfront.amazonaws.com"],
                        )
                    ],
                    actions=["s3:GetObject"],
                    resources=[bucket.arn.apply(lambda arn: arn + "/*")],
                    conditions=[
                        aws.iam.GetPolicyDocumentStatementConditionArgs(
                            test="StringEquals",
                            variable="AWS:SourceArn",
                            values=[distribution.arn],
                        )
                    ],
                )
            ],
        )
        aws.s3.BucketPolicy(
            f"{tags['project']}-{module_name}-{tags['stack']}",
            bucket=bucket.id,
            policy=document.json,
            opts=pulumi.ResourceOptions(parent=self),
        )


def main():
    LandingPageModule()


if __name__ == "__main__":
    main()
