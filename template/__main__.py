import pulumi
import pulumi_aws as aws


class Module(pulumi.ComponentResource):
    def __init__(
        self, module_name: str, opts: pulumi.ResourceOptions | None = None
    ) -> None:
        super().__init__("wenke:module:template", module_name, opts=opts)


class TemplateModule(Module):
    def __init__(
        self,
        module_name: str,
        virginia: aws.Provider = None,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        self.virginia = virginia
        super().__init__(module_name, opts)

        domain = f"{module_name}.wenke-studio.com"

        bucket = aws.s3.Bucket(
            module_name,
            opts=pulumi.ResourceOptions(parent=self),
        )

        origin_access_control = aws.cloudfront.OriginAccessControl(
            module_name,
            origin_access_control_origin_type="s3",
            signing_behavior="always",
            signing_protocol="sigv4",
            opts=pulumi.ResourceOptions(parent=self),
        )
        distribution = aws.cloudfront.Distribution(
            module_name,
            # Settings
            enabled=True,
            comment=domain,  # Description
            aliases=[domain],  # CNAME
            default_root_object="index.html",
            http_version="http1.1",
            is_ipv6_enabled=True,
            price_class="PriceClass_100",
            viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
                acm_certificate_arn=self.certificate.arn,
                ssl_support_method="sni-only",
                minimum_protocol_version="TLSv1.2_2021",
            ),
            # Origin
            origins=[
                aws.cloudfront.DistributionOriginArgs(
                    domain_name=bucket.bucket_regional_domain_name,
                    origin_id=bucket.id,
                    origin_access_control_id=origin_access_control.id,
                )
            ],
            # Behavior
            default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
                allowed_methods=["GET", "HEAD"],
                cached_methods=["GET", "HEAD"],
                viewer_protocol_policy="redirect-to-https",
                compress=True,
                target_origin_id=bucket.id,
                cache_policy_id=self.cache_policy.id,
                # origin_request_policy_id=
                response_headers_policy_id=self.response_header_policy.id,
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
            domain,
            zone_id=self.zone.id,
            name=domain,  # distribution.aliases[0]
            type="CNAME",
            ttl=300,
            records=[distribution.domain_name],
            opts=pulumi.ResourceOptions(parent=self),
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
            module_name,
            bucket=bucket.id,
            policy=document.json,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs({})

    @property
    def certificate(self) -> aws.acm.AwaitableGetCertificateResult:
        return aws.acm.get_certificate(
            domain="*.wenke-studio.com",
            opts=pulumi.InvokeOptions(provider=self.virginia),
        )

    @property
    def cache_policy(self) -> aws.cloudfront.AwaitableGetCachePolicyResult:
        return aws.cloudfront.get_cache_policy(
            name="Managed-CachingOptimized",
        )

    @property
    def response_header_policy(
        self,
    ) -> aws.cloudfront.AwaitableGetResponseHeadersPolicyResult:
        return aws.cloudfront.get_response_headers_policy(
            name="Managed-SecurityHeadersPolicy"
        )

    @property
    def zone(self) -> aws.route53.AwaitableGetZoneResult:
        return aws.route53.get_zone(
            name="wenke-studio.com",
        )


def main():
    virginia = aws.Provider(resource_name="virginia", region="us-east-1")

    TemplateModule(module_name="neon", virginia=virginia)
    TemplateModule(module_name="dark", virginia=virginia)


if __name__ == "__main__":
    main()
