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

"""Handles all requests to the conductor service."""

from oslo.config import cfg

from savanna.conductor import manager
from savanna.conductor import resource as r
from savanna.openstack.common import log as logging

conductor_opts = [
    cfg.BoolOpt('use_local',
                default=True,
                help='Perform savanna-conductor operations locally'),
]

conductor_group = cfg.OptGroup(name='conductor',
                               title='Conductor Options')

CONF = cfg.CONF
CONF.register_group(conductor_group)
CONF.register_opts(conductor_opts, conductor_group)

LOG = logging.getLogger(__name__)


def _get_id(obj):
    """Return object id.

    Allows usage of both an object or an object's ID as a parameter when
    dealing with relationships.
    """
    try:
        return obj.id
    except AttributeError:
        return obj


class LocalApi(object):
    """A local version of the conductor API that does database updates
    locally instead of via RPC.
    """

    def __init__(self):
        self._manager = manager.ConductorManager()

    ## Cluster ops

    @r.wrap(r.ClusterResource)
    def cluster_get(self, context, cluster):
        """Return the cluster or None if it does not exist."""
        return self._manager.cluster_get(context, _get_id(cluster))

    @r.wrap(r.ClusterResource)
    def cluster_get_all(self, context):
        """Get all clusters."""
        return self._manager.cluster_get_all(context)

    @r.wrap(r.ClusterResource)
    def cluster_create(self, context, values):
        """Create a cluster from the values dictionary.
        Return the created cluster.
        """
        return self._manager.cluster_create(context, values)

    def cluster_update(self, context, cluster, values):
        """Update the cluster with the given values dictionary.
        Populate provided cluster object with updated values.
        Return None.
        """
        new_cluster = self._manager.cluster_update(context, _get_id(cluster),
                                                   values)
        cluster.re_init(new_cluster)

    def cluster_destroy(self, context, cluster):
        """Destroy the cluster or raise if it does not exist.
        Return None.
        """
        self._manager.cluster_destroy(context, _get_id(cluster))

    ## Node Group ops

    def node_group_add(self, context, cluster, values):
        """Create a node group from the values dictionary.
        Populate provided cluster object with new node group.
        Return ID of the created node group.
        """
        new_cluster = self._manager.node_group_add(context, _get_id(cluster),
                                                   values)
        cluster.re_init(new_cluster)
        return cluster.node_groups[-1].id

    def node_group_update(self, context, node_group, values):
        """Update the node group with the given values dictionary.
        Populate provided node group object with updated values.
        Return None.
        """
        new_ng = self._manager.node_group_update(context, _get_id(node_group),
                                                 values)
        node_group.re_init(new_ng)

    def node_group_remove(self, context, node_group):
        """Destroy the node group or raise if it does not exist.
        Return None.
        """
        self._manager.node_group_remove(context, _get_id(node_group))

    ## Instance ops

    def instance_add(self, context, node_group, values):
        """Create an instance from the values dictionary.
        Populate provided node group object with new instance.
        Return ID of the created instance.
        """
        new_ng = self._manager.instance_add(context, _get_id(node_group),
                                            values)
        node_group.re_init(new_ng)
        return node_group.instances[-1].id

    def instance_update(self, context, instance, values):
        """Update the instance with the given values dictionary.
        Populate provided instance object with updated values.
        Return None.
        """
        new_inst = self._manager.instance_update(context, _get_id(instance),
                                                 values)
        instance.re_init(new_inst)

    def instance_remove(self, context, instance):
        """Destroy the instance or raise if it does not exist.
        Return None.
        """
        self._manager.instance_remove(context, _get_id(instance))

    ## Cluster Template ops

    @r.wrap(r.ClusterTemplateResource)
    def cluster_template_get(self, context, cluster_template):
        """Return the cluster template or None if it does not exist."""
        return self._manager.cluster_template_get(context,
                                                  _get_id(cluster_template))

    @r.wrap(r.ClusterTemplateResource)
    def cluster_template_get_all(self, context):
        """Get all cluster templates."""
        return self._manager.cluster_template_get_all(context)

    @r.wrap(r.ClusterTemplateResource)
    def cluster_template_create(self, context, values):
        """Create a cluster template from the values dictionary.
        Return the created cluster template
        """
        return self._manager.cluster_template_create(context, values)

    def cluster_template_destroy(self, context, cluster_template):
        """Destroy the cluster template or raise if it does not exist.
        Return None
        """
        self._manager.cluster_template_destroy(context,
                                               _get_id(cluster_template))

    ## Node Group Template ops

    @r.wrap(r.NodeGroupResource)
    def node_group_template_get(self, context, node_group_template):
        """Return the node group template or None if it does not exist."""
        return self._manager.node_group_template_get(
            context, _get_id(node_group_template))

    @r.wrap(r.NodeGroupResource)
    def node_group_template_get_all(self, context):
        """Get all node group templates."""
        return self._manager.node_group_template_get_all(context)

    @r.wrap(r.NodeGroupResource)
    def node_group_template_create(self, context, values):
        """Create a node group template from the values dictionary.
        Return the created node group template
        """
        return self._manager.node_group_template_create(context, values)

    def node_group_template_destroy(self, context, node_group_template):
        """Destroy the node group template or raise if it does not exist.
        Return None
        """
        self._manager.node_group_template_destroy(context,
                                                  _get_id(node_group_template))

    ## Data Source ops

    @r.wrap(r.DataSource)
    def data_source_get(self, context, data_source):
        """Return the Data Source or None if it does not exist."""
        return self._manager.data_source_get(context, _get_id(data_source))

    @r.wrap(r.DataSource)
    def data_source_get_all(self, context):
        """Get all Data Sources."""
        return self._manager.data_source_get_all(context)

    @r.wrap(r.DataSource)
    def data_source_create(self, context, values):
        """Create a Data Source from the values dictionary."""
        return self._manager.data_source_create(context, values)

    def data_source_destroy(self, context, data_source):
        """Destroy the Data Source or raise if it does not exist."""
        self._manager.data_source_destroy(context, _get_id(data_source))


class RemoteApi(LocalApi):
    """Conductor API that does updates via RPC to the ConductorManager."""

    # TODO(slukjanov): it should override _manager and only necessary functions
