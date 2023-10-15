import pulumi
import pulumi_aws as aws


class DevOpsModule(pulumi.ComponentResource):
    def __init__(
        self, module_name: str, opts: pulumi.ResourceOptions | None = None
    ) -> None:
        super().__init__("wenke:module:devops", module_name, opts=opts)


class DevOps(DevOpsModule):
    def __init__(self) -> None:
        super().__init__(module_name="devops")

        available = aws.get_availability_zones(state="available")
        availability_zones = available.names[:1]

        vpc = aws.ec2.Vpc(
            "devops",
            cidr_block="10.0.0.0/16",
            enable_dns_hostnames=True,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.availability_zones = availability_zones
        self.vpc = vpc


class GitLab(DevOpsModule):
    def __init__(self, devops: DevOps) -> None:
        super().__init__(module_name="gitlab")

        aws.ec2.Subnet(
            f"gitlab-{devops.availability_zones[0]}",
            availability_zone=devops.availability_zones[0],
            vpc_id=devops.vpc.id,
            cidr_block="10.0.1.0/24",
            map_public_ip_on_launch=True,
            opts=pulumi.ResourceOptions(parent=self),
        )

        security_group = aws.ec2.SecurityGroup(
            "gitlab",
            vpc_id=devops.vpc.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        stack = "dev"
        aws.s3.Bucket(
            "gitlab",
            bucket=f"gitlab-{stack}",  # bucket is world resource
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.security_group = security_group

    def depend_on(self):
        pass


class Runner(DevOpsModule):
    def __init__(self, devops: DevOps) -> None:
        super().__init__(module_name="runner")

        aws.ec2.Subnet(
            f"runner-{devops.availability_zones[0]}",
            availability_zone=devops.availability_zones[0],
            vpc_id=devops.vpc.id,
            cidr_block="10.0.2.0/24",
            map_public_ip_on_launch=True,
            opts=pulumi.ResourceOptions(parent=self),
        )

        security_group = aws.ec2.SecurityGroup(
            "runner",
            vpc_id=devops.vpc.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.security_group = security_group

    def depend_on(self):
        pass


def main():
    # fixme: use named-resource
    pass
    # devops = DevOps()
    # GitLab(devops=devops)
    # Runner(devops=devops)


if __name__ == "__main__":
    main()
