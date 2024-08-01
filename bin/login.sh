#!/usr/bin/zsh

account="wenke-studio"

alias_name=$(aws iam list-account-aliases --query "AccountAliases[0]" --output text)
if [ "$alias_name" = "$account" ]; then
    pulumi login s3://wenke-studio-infrastructure
else
    echo "Wrong alias name: $alias_name"
fi
 