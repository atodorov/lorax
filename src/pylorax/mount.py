# mount.py
#
# Copyright (C) 2011-2015  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s): Brian C. Lane <bcl@redhat.com>
#
import logging
log = logging.getLogger("livemedia-creator")

import os

from pylorax.imgutils import mount, umount
from pylorax.executils import execWithCapture

class IsoMountpoint(object):
    """
    Mount the iso and check to make sure the vmlinuz and initrd.img files exist

    Also check the iso for a a stage2 image and set a flag and extract the
    iso's label.

    stage2 can be either LiveOS/squashfs.img or images/install.img
    """
    def __init__(self, iso_path, initrd_path=None):
        """
        Mount the iso

        :param str iso_path: Path to the iso to mount
        :param str initrd_path: Optional path to initrd

        initrd_path can be used to point to a tree with a newer
        initrd.img than the iso has. The iso is still used for stage2.

        self.kernel and self.initrd point to the kernel and initrd.
        self.stage2 is set to True if there is a stage2 image.
        self.repo is the path to the mounted iso if there is a /repodata dir.
        """
        self.label = None
        self.iso_path = iso_path
        self.initrd_path = initrd_path

        if not self.initrd_path:
            self.mount_dir = mount(self.iso_path, opts="loop")
        else:
            self.mount_dir = self.initrd_path

        self.kernel = self.mount_dir+"/isolinux/vmlinuz"
        self.initrd = self.mount_dir+"/isolinux/initrd.img"

        if os.path.isdir(self.mount_dir+"/repodata"):
            self.repo = self.mount_dir
        else:
            self.repo = None
        self.stage2 = os.path.exists(self.mount_dir+"/LiveOS/squashfs.img") or \
                      os.path.exists(self.mount_dir+"/images/install.img")

        try:
            for f in [self.kernel, self.initrd]:
                if not os.path.isfile(f):
                    raise Exception("Missing file on iso: {0}".format(f))
        except:
            self.umount()
            raise

        self.get_iso_label()

    def umount( self ):
        """Unmount the iso"""
        if not self.initrd_path:
            umount(self.mount_dir)

    def get_iso_label(self):
        """
        Get the iso's label using isoinfo

        Sets self.label if one is found
        """
        isoinfo_output = execWithCapture("isoinfo", ["-d", "-i", self.iso_path])
        log.debug(isoinfo_output)
        for line in isoinfo_output.splitlines():
            if line.startswith("Volume id: "):
                self.label = line[11:]
                return
