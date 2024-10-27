import pulumi
from pulumi_aws import alb, autoscaling, ec2, iam, s3

from .utils import create_public_subnets, create_the_service_role, resource_name


def get_default_document(
    buckets: list[s3.BucketV2],
) -> iam.AwaitableGetPolicyDocumentResult:
    document = iam.get_policy_document(
        statements=[
            iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:DeleteObject",
                    "s3:PutObjectAcl",
                ],
                resources=[
                    bucket.arn.apply(lambda arn: arn + "/*") for bucket in buckets
                ],
            ),
            iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "s3:ListBucket",
                    "s3:AbortMultipartUpload",
                    "s3:ListMultipartUploadParts",
                    "s3:ListBucketMultipartUploads",
                ],
                resources=[bucket.arn for bucket in buckets],
            ),
        ],
    )
    return document


def create_gitlab(
    vpc: ec2.Vpc,
    availability_zones: list[str],
    subnet_offset: int,
    target_group: alb.TargetGroup,
) -> ec2.SecurityGroup:
    subnets = create_public_subnets(
        resource_name("gitlab"),
        vpc=vpc,
        availability_zones=availability_zones,
        subnet_offset=subnet_offset,
    )

    security_group = ec2.SecurityGroup(
        resource_name("gitlab"),
        vpc_id=vpc.id,
    )
    ec2.SecurityGroupRule(
        resource_name("gitlab-default-outbound"),
        security_group_id=security_group.id,
        type="egress",
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
    )

    buckets = {
        "object-storage": s3.BucketV2(
            resource_name("gitlab-object-storage"),
        ),
        "backup": s3.BucketV2(
            resource_name("gitlab-backup"),
        ),
    }
    # todo: upload `gitlab.rb` to the backup bucket

    document = get_default_document(buckets=buckets.values())
    policies = {
        "default": iam.Policy(
            resource_name("gitlab-default"),
            policy=document.json,
        ),
        "ssm": iam.Policy.get(
            resource_name("gitlab-ssm"),
            id="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
        ),
    }

    role = create_the_service_role(
        resource_name("gitlab"),
        service="ec2.amazonaws.com",
        policies=policies,
    )

    ubuntu = ec2.get_ami(
        most_recent=True,
        owners=["099720109477"],
        name_regex="ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*",
    )
    user_data = ""
    profile = iam.InstanceProfile(
        resource_name("gitlab"),
        role=role.name,
    )
    launch_template = ec2.LaunchTemplate(
        resource_name("gitlab"),
        iam_instance_profile={"arn": profile.arn},
        image_id=ubuntu.id,
        user_data=user_data,
        instance_type="m5.large",
        block_device_mappings=[
            # Gitaly volume
            {
                "device_name": "/dev/sda1",
                "ebs": {
                    "delete_on_termination": True,
                    "volume_size": 100,
                    "volume_type": "gp3",
                },
            }
        ],
        vpc_security_group_ids=[security_group.id],
        update_default_version=True,
        tag_specifications=[
            {"resource_type": "instance", "tags": {"Name": resource_name("gitlab")}},
            {"resource_type": "volume", "tags": {"Name": resource_name("gitlab")}},
        ],
    )

    autoscaling.Group(
        resource_name("gitlab"),
        min_size=1,
        max_size=1,
        launch_template={"id": launch_template.id, "version": "$Latest"},
        vpc_zone_identifiers=[subnet.id for subnet in subnets],
        health_check_type="EC2",  # todo: use ELB instead of EC2
        health_check_grace_period=300,
        target_group_arns=[target_group.arn],
    )

    # !! Create a SMTP user for GitLab by manually
    # Go to SES > SMTP Settings > Create SMTP credential
    # The credential will be created as a IAM user,
    # and the access key ID and secret access key will be used in the gitlab.rb
    # https://gitlab.com/gitlab-org/gitlab/-/issues/3655

    return security_group
