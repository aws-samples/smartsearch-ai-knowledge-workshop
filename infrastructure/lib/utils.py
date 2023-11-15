import boto3

def get_value(export_name):
    cloudformation = boto3.client('cloudformation')

    # Get stack outputs
    res = cloudformation.list_exports()
    values = res['Exports']
    for val in values:
        if val['Name'] == export_name:
            return val['Value']
    
    return ''
