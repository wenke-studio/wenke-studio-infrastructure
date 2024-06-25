import pulumi
from integrator.aws import cloudfront, s3


class CloudFront:
    bucket: s3.Bucket
    distribution: cloudfront.Distribution

    def __init__(
        self, component_name: str, domain_name: str | None = None, certificate=None
    ):
        stack = pulumi.get_stack()
        resource_name = f"{component_name}-{stack}"

        bucket = s3.Bucket(resource_name, bucket=domain_name)

        five_cache_policy = cloudfront.CachePolicy(
            resource_name,
            comment="Cache policy for five minutes",
            default_ttl=300,
            max_ttl=300,
            min_ttl=60,
        )
        origin_access_control = cloudfront.S3OriginAccessControl(
            resource_name,
        )

        distribution = cloudfront.Distribution(
            resource_name,
            domain_name=domain_name,
            bucket=bucket,
            ordered_cache_policy=five_cache_policy,
            origin_access_control=origin_access_control,
            certificate=certificate,
            http_version="http2",
        )

        pulumi.export(
            f"cloudfront-{resource_name}",
            {
                "bucket": bucket.id,
                "cache_policy": five_cache_policy.id,
                "origin_access_control": origin_access_control.id,
                "distribution": distribution.id,
            },
        )

        self.bucket = bucket
        self.distribution = distribution
