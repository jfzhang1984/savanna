# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from savanna import context
import savanna.tests.unit.conductor.manager.base as test_base

SAMPLE_DATA_SOURCE = {
    "tenant_id": "test_tenant",
    "name": "ngt_test",
    "description": "test_desc",
    "type": "Cassandra",
    "url": "localhost:1080",
    "credentials": {
        "user": "test",
        "password": "123"
    }
}


class DataSourceTest(test_base.ConductorApiTestCase):
    def test_crud_operation_create_list_delete(self):
        ctx = context.ctx()
        self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)

        lst = self.api.data_source_get_all(ctx)
        self.assertEquals(len(lst), 1)

        ds_id = lst[0]['id']
        self.api.data_source_destroy(ctx, ds_id)

        lst = self.api.data_source_get_all(ctx)
        self.assertEquals(len(lst), 0)

    def test_duplicate_data_source_create(self):
        ctx = context.ctx()
        self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)
        with self.assertRaises(RuntimeError):
            self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)

    def test_data_source_fields(self):
        ctx = context.ctx()
        ds_db_obj_id = self.api.data_source_create(ctx,
                                                   SAMPLE_DATA_SOURCE)['id']

        ds_db_obj = self.api.data_source_get(ctx, ds_db_obj_id)
        self.assertIsInstance(ds_db_obj, dict)

        for key, val in SAMPLE_DATA_SOURCE.items():
            self.assertEqual(val, ds_db_obj.get(key),
                             "Key not found %s" % key)

    def test_data_source_delete(self):
        ctx = context.ctx()
        db_obj_ds = self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)
        _id = db_obj_ds['id']

        self.api.data_source_destroy(ctx, _id)

        with self.assertRaises(RuntimeError):
            self.api.data_source_destroy(ctx, _id)
