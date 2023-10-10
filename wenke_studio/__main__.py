import pulumi
import pulumi_aws as aws


def main():
    root = aws.s3.BucketV2(
        "root",
        bucket="wenke-studio-infrastructure",
        opts=pulumi.ResourceOptions(protect=True),
    )

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

    wenke_lai = aws.iam.UserGroupMembership(
        "wenke_lai",
        user="wenke.lai",
        groups=["human", "owner"],
        opts=pulumi.ResourceOptions(protect=True),
    )


if __name__ == "__main__":
    main()
