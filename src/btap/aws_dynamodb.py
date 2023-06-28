import botocore
import logging
import os
from decimal import Decimal
from src.btap.common_paths import CommonPaths
import json
import pandas
import pathlib
import plotly.express as px
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

    def save_dict_result(self, run_options):
        table = AWSCredentials().dynamodb_resource.Table(self.table_name)
        with table.batch_writer() as batch:
            batch.put_item(json.loads(json.dumps(run_options), parse_float=Decimal))

    def dump_table(self, folder_path=None, type=None, analysis_name=None, save_output = True):
        filepath = pathlib.Path(os.path.join(folder_path, f"database.{type}"))
        failed_filepath = pathlib.Path(os.path.join(folder_path, f"database_failed.{type}"))
        filepath.parent.mkdir(parents=True, exist_ok=True)
        table = AWSCredentials().dynamodb_resource.Table(self.table_name)
        response = table.scan()
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        df = pandas.json_normalize(data)
        if analysis_name is not None:
            df = df.loc[df[':analysis_name'] == analysis_name]



        if save_output:
            if df.empty:
                print('AWS Database is empty! Nothing to dump.')
            else:
                unique_failures = df.loc[df['status'] == 'FAILED']  # [[':datapoint_id', 'container_error', 'run_options', 'datapoint_output_url']]
                if type == 'csv':
                    # Results
                    df.to_csv(filepath)
                    # Failures
                    unique_failures.to_csv(failed_filepath)
                if type == 'pickle':
                    df.to_pickle(filepath)
                    unique_failures.to_pickle(failed_filepath)
                print(f"Dumped results to {filepath}")

        return df

    def aws_db_analyses_status(self):
        table = AWSCredentials().dynamodb_resource.Table(self.table_name)
        response = table.scan()
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        df = pandas.json_normalize(data)
        if df.empty:
            print('No results yet! No status to display.')
            exit(0)
        df = df[['status', ':analysis_name']]
        status_list = list()
        # Get Analysis names
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
                'RUNNING',
                'FAILED',
                'SUCCEEDED'
            ]:
                row[status] = len(temp[temp.status == status])
            status_list.append(row)
        result = pandas.DataFrame(status_list)
        return result

    def aws_db_failures(self, analysis_name=None):
        table = AWSCredentials().dynamodb_resource.Table(self.table_name)
        response = table.scan()
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        df = pandas.json_normalize(data)
        if analysis_name is not None:
            df = df.loc[df[':analysis_name'] == analysis_name]
        if df.empty:
            print('No results yet! No status to display.')
            exit(0)

        failed_runs = df.loc[df['status'] == 'FAILED']
        unique_failures = failed_runs.drop_duplicates('container_error')
        if failed_runs.empty:
            print('No failures yet!')
            exit(0)
        return unique_failures[[':datapoint_id', 'container_error', 'run_options', 'datapoint_output_url']]

    def aws_db_analyses_chart_scatter(self,
                                      analysis_name=None,
                                      x=None,
                                      y=None,
                                      color=None,
                                      size=None,
                                      hover_data=[':datapoint_id']):
        table = AWSCredentials().dynamodb_resource.Table(self.table_name)
        response = table.scan()
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])

        df = pandas.json_normalize(data)
        if analysis_name is not None:
            df = df.loc[df[':analysis_name'] == analysis_name]
        fig = px.scatter(data_frame=df,
                         x=x,
                         y=y,
                         color=color,
                         size=size,
                         hover_data=hover_data
                         )
        fig.show()
