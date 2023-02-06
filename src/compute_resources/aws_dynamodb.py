import boto3
import botocore
import logging
import os
from decimal import Decimal
from src.compute_resources.common_paths import CommonPaths
import json
import pandas
from icecream import ic
class AWSDynamodb():
    def __init__(self):
        self.dyn_resource = boto3.resource('dynamodb')
        self.table_name = f"{CommonPaths().get_username()}_results"
        self.table = None


    def create_results_table(self):
        try:
            table = self.dyn_resource.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': ':datapoint_id', 'KeyType': 'HASH'},  # Partition key
                    {'AttributeName': ':analysis_name', 'KeyType': 'RANGE'}  # Sort key
                ],
                AttributeDefinitions=[
                    {'AttributeName': ':datapoint_id', 'AttributeType': 'S'},
                    {'AttributeName': ':analysis_name', 'AttributeType': 'S'}
                ],
                BillingMode="PAY_PER_REQUEST"
            )
            table.wait_until_exists()
        except botocore.exceptions.ClientError as err:
            logging.error(
                "Couldn't create table %s. Here's why: %s: %s", self.table_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return self.table

    def delete_results_table(self):
        table = self.dyn_resource.Table(self.table_name)
        table.delete()
        print(f"Deleting {table.name}...")
        table.wait_until_not_exists()

    def save_results(self, dataframe):
        table = self.dyn_resource.Table(self.table_name)
        with table.batch_writer() as batch:
            for index, row in dataframe.iterrows():
                ic(json.loads(row.to_json()))
                batch.put_item(json.loads(row.to_json(), parse_float=Decimal))

    def dump_results_table(self, folder_path=None, type=None):

        filepath = os.path.join(folder_path, f"database.{type}")
        table = self.dyn_resource.Table(self.table_name)
        response = table.scan()
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        df = pandas.json_normalize (data)
        if type =='csv':
            df.to_csv(filepath)
        if type =='pickle':
            df.to_pickle(filepath)

        print(f"Dumped results to {filepath}")

