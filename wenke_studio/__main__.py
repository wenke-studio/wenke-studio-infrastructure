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


if __name__ == "__main__":
    main()
