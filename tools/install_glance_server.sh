#!/bin/bash
apt-get install glance*
glance-manage  db_sync
service glance-api restart && service glance-registry restart