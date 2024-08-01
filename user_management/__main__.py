import pulumi
from pulumi_aws import cognito

STACK = pulumi.get_stack()

DOMAIN = "wenke-studio.com"
SUBDOMAIN = "auth"


def _(name: str) -> str:
    return f"{name}-{STACK}"


def main():
    domain = f"{_(SUBDOMAIN)}.{DOMAIN}"

    user_pool = cognito.UserPool(
        _("user-management"),
        username_attributes=["email"],
        mfa_configuration="OFF",
        password_policy=cognito.UserPoolPasswordPolicyArgs(
            temporary_password_validity_days=7,
            minimum_length=8,
            require_numbers=True,
            require_symbols=False,
            require_lowercase=True,
            require_uppercase=True,
        ),
        account_recovery_setting=cognito.UserPoolAccountRecoverySettingArgs(
            recovery_mechanisms=[
                cognito.UserPoolAccountRecoverySettingRecoveryMechanismArgs(
                    name="verified_email",  # can be of the following: verified_email, verified_phone_number and admin_only
                    priority=1,
                )
            ]
        ),
    )


if __name__ == "__main__":
    main()
