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
                    # can be of the following: verified_email, verified_phone_number and admin_only
                    name="verified_email",
                    priority=1,
                )
            ]
        ),
    )

    google_identity_provider = cognito.IdentityProvider(
        _("user-management"),
        user_pool_id=user_pool.id,
        provider_name="Google",
        provider_type="Google",
        provider_details={
            "authorize_scopes": "email",
            "client_id": "your client_id",
            "client_secret": "your client_secret",
        },
        attribute_mapping={
            "email": "email",
            "username": "sub",
        },
    )
    user_pool_client = cognito.UserPoolClient(
        _("user-management"),
        user_pool_id=user_pool.id,
        generate_secret=False,
        callback_urls=[
            "https://example.com/callback",
        ],
        logout_urls=[
            "https://example.com/logout",
        ],
        allowed_oauth_flows=[
            "code",
            "implicit",
        ],
        allowed_oauth_scopes=[
            "email",
            "openid",
        ],
        # options: COGNITO | SAML | Facebook | Google | LoginWithAmazon | SignInWithApple | OIDC
        supported_identity_providers=["COGNITO", "Google"],
    )


if __name__ == "__main__":
    main()
