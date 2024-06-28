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


if __name__ == "__main__":
    main()
