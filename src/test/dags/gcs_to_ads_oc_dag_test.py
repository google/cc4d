# python3
# coding=utf-8
# Copyright 2020 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test for dags.gcs_to_ads_oc_dag.
"""

import unittest

from airflow.contrib.hooks import bigquery_hook
from airflow.contrib.hooks import gcp_api_base_hook
from airflow.models import baseoperator
from airflow.models import dag
from airflow.models import variable
import mock

from dags import gcs_to_ads_oc_dag
from plugins.pipeline_plugins.hooks import monitoring_hook

_DAG_NAME = gcs_to_ads_oc_dag._DAG_NAME

AIRFLOW_VARIABLES = {
    'dag_name': _DAG_NAME,
    f'{_DAG_NAME}_schedule': '@once',
    f'{_DAG_NAME}_retries': 0,
    f'{_DAG_NAME}_retry_delay': 3,
    f'{_DAG_NAME}_is_retry': True,
    f'{_DAG_NAME}_is_run': True,
    f'{_DAG_NAME}_enable_run_report': False,
    f'{_DAG_NAME}_enable_monitoring': True,
    f'{_DAG_NAME}_enable_monitoring_cleanup': False,
    'monitoring_data_days_to_live': 50,
    'monitoring_dataset': 'test_monitoring_dataset',
    'monitoring_table': 'test_monitoring_table',
    'monitoring_bq_conn_id': 'test_monitoring_conn',
    'gcs_bucket_name': 'test_bucket',
    'gcs_bucket_prefix': 'test_dataset',
    'gcs_content_type': 'JSON',
    'ads_credentials': ('adwords:\n'
                        '  client_customer_id: 123-456-7890\n'
                        '  developer_token: abcd\n'
                        '  client_id: test.apps.googleusercontent.com\n'
                        '  client_secret: secret\n'
                        '  refresh_token: 1//token\n'),
}


class DAGTest(unittest.TestCase):

  def setUp(self):
    super(DAGTest, self).setUp()
    self.addCleanup(mock.patch.stopall)

    self.mock_variable = mock.patch.object(
        variable, 'Variable', autospec=True).start()
    # `side_effect` is assigned to `lambda` to dynamically return values
    # each time when self.mock_variable is called.
    self.mock_variable.get.side_effect = (
        lambda key, value: AIRFLOW_VARIABLES[key])

    self.original_gcp_hook_init = gcp_api_base_hook.GoogleCloudBaseHook.__init__
    gcp_api_base_hook.GoogleCloudBaseHook.__init__ = mock.MagicMock()

    self.original_bigquery_hook_init = bigquery_hook.BigQueryHook.__init__
    bigquery_hook.BigQueryHook.__init__ = mock.MagicMock()

    self.original_monitoring_hook = monitoring_hook.MonitoringHook
    monitoring_hook.MonitoringHook = mock.MagicMock()

  def tearDown(self):
    super().tearDown()
    gcp_api_base_hook.GoogleCloudBaseHook.__init__ = self.original_gcp_hook_init
    bigquery_hook.BigQueryHook.__init__ = self.original_bigquery_hook_init
    monitoring_hook.MonitoringHook = self.original_monitoring_hook

  def test_create_dag(self):
    """Tests that returned DAG contains correct DAG and tasks."""
    expected_task_ids = ['gcs_to_ads_oc_retry_task', 'gcs_to_ads_oc_task']

    test_dag = gcs_to_ads_oc_dag.GCSToAdsOCDag(
        AIRFLOW_VARIABLES['dag_name']).create_dag()

    self.assertIsInstance(test_dag, dag.DAG)
    self.assertEqual(len(test_dag.tasks), len(expected_task_ids))
    for task in test_dag.tasks:
      self.assertIsInstance(task, baseoperator.BaseOperator)
    actual_task_ids = [t.task_id for t in test_dag.tasks]
    self.assertListEqual(actual_task_ids, expected_task_ids)


if __name__ == '__main__':
  unittest.main()
