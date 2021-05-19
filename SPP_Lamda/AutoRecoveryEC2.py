from collections import defaultdict
import boto3
import json
ec2 = boto3.resource('ec2')
client = boto3.client('ec2')

def get_instance_tag(fid, keyName):
	ec2 = boto3.resource('ec2')
	ec2instance = ec2.Instance(fid)
	tagValue = ''
	for tags in ec2instance.tags:
		if tags['Key'] == keyName:
			tagValue = tags['Value']
			break
	return tagValue
def lambda_handler(event, context):
	ec2 = boto3.resource('ec2')
	message = event['Records'][0]['Sns']['Message']
	InstanceID = json.loads(message)['Trigger']['Dimensions'][0]['value']
	region = json.loads(message)['Region']
	tagName = get_instance_tag(InstanceID, 'Name')
	InstanceEC2 = ec2.Instance(id=InstanceID)
	if not bool(InstanceID):
		raise Exception('Instances are not defined!')
	if not bool(region):
		raise Exception('Region is not defined!')
	tagReboot = get_instance_tag(InstanceID, 'AutoRecoveryEC2')
	print(tagReboot)
	if 'true' == tagReboot.lower():
		snsMessage = 'The instance is allowed to restart automatically when Status check failed:\n'
		snsMessage += '\nregion = %s\ninstance id = %s\ntag Name = %s'% (region, InstanceID, tagName)
		InstanceEC2.stop(
			Force=True
		)
		print 'started your stopping:'
		InstanceEC2.wait_until_stopped(
			Filters=[
						{
							'Name': 'instance-state-name',
							'Values': ['stopped']
						}
					],
			)
		InstanceEC2.start()
	else:
		snsMessage = 'The instance is not allowed to restart automatically when Status check failed:\n'
		snsMessage += '\nregion = %s\ninstance id = %s\ntag Name = %s' % (region, instanceId, tagName)
	print snsMessage
	# Send Notification
	sns = boto3.client('sns', 'cn-north-1')
	sns.publish(
		TopicArn = 'arn:aws-cn:sns:cn-north-1:863228431998:EC2-AutoRecoveryEC2-Email',
		Subject = '[cn-north-1][SPP-PRD]Notification for EC2 auto restart when status check failed',
		Message = snsMessage
	)