from collections import defaultdict
from collections import defaultdict
import boto3, os, json, datetime
from botocore.exceptions import ClientError

# Define global variable
region_Name = 'cn-north-1'
key_Age = 90
sns_Topic = 'arn:aws-cn:sns:cn-north-1:863228431998:IAM-AcessKey-ExpireDate'


def get_usr_old_keys(keyAge, snsTopic):
    client = boto3.client('iam', region_name=region_Name)
    snsClient = boto3.client('sns', region_name=region_Name)
    usersList = client.list_users()

    timeLimit = datetime.datetime.now() - datetime.timedelta(days=int(keyAge))
    usrsWithOldKeys = {'Users': [],
                       'Description': 'List of users with Key Age greater than (>=) {} days'.format(keyAge),
                       'KeyAgeCutOff': keyAge}
    # Iterate through list of users and compare with `key_age` to flag old key owners
    for k in usersList['Users']:
        accessKeys = client.list_access_keys(UserName=k['UserName'])
        # Iterate for all users
        for key in accessKeys['AccessKeyMetadata']:
            if key['CreateDate'].date() <= timeLimit.date():
                usrsWithOldKeys['Users'].append({'UserName': k['UserName'], 'KeyAgeInDays': (
                            datetime.date.today() - key['CreateDate'].date()).days})

        # If no users found with older keys, add message in response
        if not usrsWithOldKeys['Users']:
            usrsWithOldKeys['OldKeyCount'] = 'Found 0 Keys that are older than {} days'.format(keyAge)
        else:
            usrsWithOldKeys['OldKeyCount'] = 'Found {0} Keys that are older than {1} days'.format(
                len(usrsWithOldKeys['Users']), keyAge)
    try:
        snsClient.get_topic_attributes(TopicArn=snsTopic)
        snsClient.publish(TopicArn=snsTopic, Message=json.dumps(usrsWithOldKeys, indent=4),
                          Subject='[SPP-PROD-CN] List IAM users have old access key')
        usrsWithOldKeys['SecOpsEmailed'] = "Yes"
    except ClientError as e:
        usrsWithOldKeys['SecOpsEmailed'] = "No - SecOpsTopicArn is Incorrect"
    return usrsWithOldKeys


def lambda_handler(event, context):
    return get_usr_old_keys(key_Age, sns_Topic)