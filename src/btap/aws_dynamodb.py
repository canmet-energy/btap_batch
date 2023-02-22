import botocore
import logging
import os
from decimal import Decimal
from src.btap.common_paths import CommonPaths
import json
import pandas
from icecream import ic
from src.btap.aws_credentials import AWSCredentials


class AWSResultsTable():
    def __init__(self):
        self.table = None
        self.table_name = f"{CommonPaths().get_username()}_results"
        self.key_schema = [
            {'AttributeName': ':datapoint_id', 'KeyType': 'HASH'},  # Partition key
            {'AttributeName': ':analysis_name', 'KeyType': 'RANGE'}  # Sort key
        ]
        self.attribute_defs = [
            {'AttributeName': ':datapoint_id', 'AttributeType': 'S'},
            {'AttributeName': ':analysis_name', 'AttributeType': 'S'}
        ]
        self.billing_mode = "PAY_PER_REQUEST"

    def create_table(self):
        if not self.table_name in AWSCredentials().dynamodb_client.list_tables()['TableNames']:
            try:
                table = AWSCredentials().dynamodb_resource.create_table(
                    TableName=self.table_name,
                    KeySchema=self.key_schema,
                    AttributeDefinitions=self.attribute_defs,
                    BillingMode=self.billing_mode
                )
                table.wait_until_exists()
            except botocore.exceptions.ClientError as err:
                logging.error(
                    "Couldn't create table %s. Here's why: %s: %s", self.table_name,
                    err.response['Error']['Code'], err.response['Error']['Message'])
                raise
            else:
                return self.table

    def delete_table(self):
        if self.table_name in AWSCredentials().dynamodb_client.list_tables()['TableNames']:
            table = AWSCredentials().dynamodb_resource.Table(self.table_name)
            table.delete()
            print(f"Deleting {table.name}...")
            table.wait_until_not_exists()

    def save_results(self, dataframe):
        table = AWSCredentials().dynamodb_resource.Table(self.table_name)
        with table.batch_writer() as batch:
            for index, row in dataframe.iterrows():
                batch.put_item(json.loads(row.to_json(), parse_float=Decimal))

    def save_dict_result(self,run_options):
        table = AWSCredentials().dynamodb_resource.Table(self.table_name)
        with table.batch_writer() as batch:
            batch.put_item(json.loads(json.dumps(run_options), parse_float=Decimal))




    def dump_table(self, folder_path=None, type=None):

        filepath = os.path.join(folder_path, f"database.{type}")
        table = AWSCredentials().dynamodb_resource.Table(self.table_name)
        response = table.scan()
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        df = pandas.json_normalize(data)
        if type == 'csv':
            df.to_csv(filepath)
        if type == 'pickle':
            df.to_pickle(filepath)
        print(f"Dumped results to {filepath}")



    def aws_db_analyses_dashboard(self):
        table = AWSCredentials().dynamodb_resource.Table(self.table_name)
        response = table.scan()
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        df = pandas.json_normalize(data)
        df = df[['status', ':analysis_name', ':datapoint_id', 'container_error','datapoint_output_url']]
        status_list = list()
        #Get Analysis names
        analysis_names = sorted(df[':analysis_name'].unique())
        for analysis_name in analysis_names:
            temp = df.loc[df[':analysis_name'] == analysis_name]
            row = dict()
            row[':analysis_name'] = analysis_name
            for status in [
                           'SUBMITTED',
                           'PENDING',
                           'RUNNABLE',
                           'STARTING',
                           'FAILED',
                           'SUCCEEDED'
            ]:
                row[status] = len(temp[temp.status == status])
            status_list.append(row)
        result = pandas.DataFrame(status_list)
        return result

    def aws_db_list_failures(self, analysis_name=None):
        table = AWSCredentials().dynamodb_resource.Table(self.table_name)
        response = table.scan()
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        df = pandas.json_normalize(data)
        df = df[['status', ':analysis_name', ':datapoint_id', 'container_error','datapoint_output_url']]
        if analysis_name is not None:
            df = df.loc[df[':analysis_name'] == analysis_name]
        failed_runs = df.loc[df['status'] == 'FAILED'][['status', ':analysis_name', ':datapoint_id', 'container_error','datapoint_output_url']]
        return failed_runs






