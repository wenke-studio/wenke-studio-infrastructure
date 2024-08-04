import pulumi
import pulumi_aws as aws


class IAM:
    def __init__(self) -> None:
        owner = aws.iam.Group(
            "owner",
            name="owner",
            opts=pulumi.ResourceOptions(protect=True),
        )

        human = aws.iam.Group(
            "human",
            name="human",
            opts=pulumi.ResourceOptions(protect=True),
        )

        wenke_lai = aws.iam.User(
            "wenke_lai",
            name="wenke.lai",
            opts=pulumi.ResourceOptions(protect=True),
        )

        aws.iam.UserGroupMembership(
            "wenke_lai",
            user=wenke_lai.name,
            groups=[human.name, owner.name],
            opts=pulumi.ResourceOptions(protect=True),
        )


def create_static_website_for_a_record(zone: aws.route53.Zone):
    resource_name = "root-record"

    bucket = aws.s3.BucketV2(
        resource_name,
        # The name of the bucket is the same as the name of the record that you're creating
        bucket="wenke-studio.com",
    )
    aws.s3.BucketObjectv2(
        resource_name,
        bucket=bucket.id,
        key="index.html",
        source=pulumi.FileAsset("index.html"),
    )
    website = aws.s3.BucketWebsiteConfigurationV2(
        resource_name,
        bucket=bucket.id,
        index_document={
            "suffix": "index.html",
        },
    )

    aws.s3.BucketPublicAccessBlock(
        resource_name,
        bucket=bucket.id,
        block_public_acls=False,
        block_public_policy=False,
        ignore_public_acls=False,
        restrict_public_buckets=False,
    )
    aws.s3.BucketPolicy(
        "bucket-policy",
        bucket=bucket.id,
        policy=bucket.arn.apply(
            lambda arn: {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": [f"{arn}/*"],
                    }
                ],
            }
        ),
    )

    aws.route53.Record(
        resource_name,
        zone_id=zone.zone_id,
        type="A",
        name="wenke-studio.com",  # A record's name is root domain
        aliases=[
            {
                "name": website.website_domain,
                "zoneId": bucket.hosted_zone_id,
                "evaluate_target_health": False,
            }
        ],
    )


def main():
    IAM()

    aws.s3.BucketV2(
        "root",
        bucket="wenke-studio-infrastructure",
        opts=pulumi.ResourceOptions(protect=True),
    )

    wenke_studio = aws.route53.Zone(
        "wenke_studio",
        comment="HostedZone created by Route53 Registrar",
        name="wenke-studio.com",
        opts=pulumi.ResourceOptions(protect=True),
    )
    pulumi.export("zone", wenke_studio.id)

    virginia = aws.Provider("virginia", region="us-east-1")
    certificate = aws.acm.Certificate(
        "certificate",
        domain_name="*.wenke-studio.com",
        validation_method="DNS",
        opts=pulumi.ResourceOptions(provider=virginia, protect=True),
    )
    validation = certificate.domain_validation_options[0]
    aws.route53.Record(
        "validation-record",
        name=validation.resource_record_name,
        zone_id=wenke_studio.zone_id,
        type=validation.resource_record_type,
        records=[validation.resource_record_value],
        ttl=300,
    )
    pulumi.export(
        "certificate",
        "arn:aws:acm:us-east-1:426352940371:certificate/383e1e78-5986-46c5-bdcc-951d5fad5207",
    )

    create_static_website_for_a_record(wenke_studio)


if __name__ == "__main__":
    main()
