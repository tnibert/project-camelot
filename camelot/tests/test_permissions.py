from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.shortcuts import reverse
from django.http import Http404

import os
import shutil

from ..controllers.albumcontroller import albumcontroller
from ..controllers.groupcontroller import groupcontroller
from ..controllers.utilities import PermissionException
from ..constants import *
from ..view import album
from .helperfunctions import complete_add_friends

"""
In this file we need to define what our access permissions need to be
and test correct access and access violations

Access types:
Public, All Friends, Groups, Private
public - everyone can view
all friends - all friends can view (DEFAULT)
groups - only group members can view
private - only owner and contributors can view

Album:
If album has no groups, default is all friends? - not current implementation
Contributor can always view album

To validate an album:
Check if accessing user is in album's groups

Todo:
    - check access rights for edit and manage endpoints
    - check access rights for viewing and uploading photos

Requirements:
    - not logged in
        - can view public album
    - logged in not friend
        - can view public, album
    - logged in friend not in group
        - can view public, all friends album
    - logged in friend in group
        - can view public, all friends, groups album
    - logged in contributor
        - can view all access types
        - can view manage page
        - can add/remove own groups if access type is groups
        - can add photos to album
    - logged in owner
        - can view all access types
        - can view manage page
        - can edit album access type
        - can add/remove own groups
        - can add/remove contributors
        - can add photos to album
"""

#class test_controller_permissions(TestCase):
#    pass

class PermissionTestCase(TestCase):
    """
    Scaffolding for permissions tests
    """
    def setUp(self):
        self.credentials = {
            'username': 'testuser',
            'email': 'user@test.com',
            'password': 'secret'}
        self.u = User.objects.create_user(**self.credentials)
        self.u.save()

        self.credentials2 = {
            'username': 'testuser2',
            'email': 'user2@test.com',
            'password': 'secret'}
        self.u2 = User.objects.create_user(**self.credentials2)
        self.u2.save()

        # send login data
        # response = self.client.post('', self.credentials, follow=True)

        self.factory = RequestFactory()

        # create album for self.u
        self.albumcontrol = albumcontroller(self.u.id)
        self.testalbum = self.albumcontrol.create_album("test name", "test description")

        # create a group for self.u
        self.groupcontrol = groupcontroller(self.u.id)
        self.testgroup = self.groupcontrol.create("test group")

        # add group to album
        self.albumcontrol.add_group_to_album(self.testalbum, self.testgroup)

    def make_logged_in_not_friend(self):
        # log in
        response = self.client.post('', self.credentials2, follow=True)

    def make_logged_in_friend_not_in_group(self):

        complete_add_friends(self.u.id, self.u2.id)

        response = self.client.post('', self.credentials2, follow=True)

    def make_logged_in_friend_in_group(self):

        complete_add_friends(self.u.id, self.u2.id)
        self.groupcontrol.add_member(self.testgroup.id, self.u2.profile)

        response = self.client.post('', self.credentials2, follow=True)

    def make_logged_in_contributor(self):

        # add as contributor before adding friend
        # this unit test should be elsewhere
        assert not self.albumcontrol.add_contributor_to_album(self.testalbum, self.u2.profile)

        complete_add_friends(self.u.id, self.u2.id)

        assert self.albumcontrol.add_contributor_to_album(self.testalbum, self.u2.profile)

        response = self.client.post('', self.credentials2, follow=True)

    def make_logged_in_owner(self):
        """
        Login as album creator (owner) and access all access types
        """
        response = self.client.post('', self.credentials, follow=True)

    def perm_escalate_helper(self, albumcontrol, request, testalbum, id, user, func, level):
        """
        Incrementally tighten permissions for album
        :param albumcontrol: albumcontroller object
        :param request: request to test against
        :param testalbum: album to raise permissions of
        :param id: function arg to test against
        :param user: user to test against
        :param func: function matching request
        :param level: level of access user should have
                1: public
                2: all friends
                3: groups
                4: private
                -- defined in constants --
        """
        # assign anonymous user to requests
        request.user = user

        albumcontrol.set_accesstype(testalbum, ALBUM_PUBLIC)

        if level >= ALBUM_PUBLIC:
            response = func(request, id)
            self.assertEqual(response.status_code, 200)
        else:
            self.assertRaises(PermissionException, func, request, id)

        albumcontrol.set_accesstype(testalbum, ALBUM_ALLFRIENDS)

        if level >= ALBUM_ALLFRIENDS:
            response = func(request, id)
            self.assertEqual(response.status_code, 200)
        else:
            self.assertRaises(PermissionException, func, request, id)

        albumcontrol.set_accesstype(testalbum, ALBUM_GROUPS)

        if level >= ALBUM_GROUPS:
            response = func(request, id)
            self.assertEqual(response.status_code, 200)
        else:
            self.assertRaises(PermissionException, func, request, id)

        albumcontrol.set_accesstype(testalbum, ALBUM_PRIVATE)

        if level >= ALBUM_PRIVATE:
            response = func(request, id)
            self.assertEqual(response.status_code, 200)
        else:
            self.assertRaises(PermissionException, func, request, id)


class AlbumPhotoViewPermissionsTest(PermissionTestCase):
    """
    Test album view and photo view permissions
    Covers show_album, show_photo, and present_photo
    """
    def setUp(self):

        super(AlbumPhotoViewPermissionsTest, self).setUp()

        self.testdir = "testdir"

        # add photo to album
        if not os.path.exists(self.testdir):
            os.makedirs(self.testdir)
        os.chdir(self.testdir)

        with open('../camelot/tests/resources/testimage.jpg', 'rb') as fi:
            self.photo = self.albumcontrol.add_photo_to_album(self.testalbum.id, "our test album", fi)

        # define requests to test
        self.showalbumrequest = self.factory.get(reverse("show_album", kwargs={'id': self.testalbum.id}))
        self.photorequest = self.factory.get(reverse("show_photo", kwargs={'photoid': self.photo.id}))
        self.indivphotorequest = self.factory.get(reverse("present_photo", kwargs={'photoid': self.photo.id}))


    def tearDown(self):
        os.chdir("..")
        shutil.rmtree(self.testdir)

    def test_not_logged_in(self):
        """
        Can view public album only
        test can view public photo
        - Photo view inherits permission from album
        Cannot view other access types
        cannot edit album or upload photos
        Cannot add non logged in user to group
        """

        # test show album
        self.perm_escalate_helper(self.albumcontrol, self.showalbumrequest, self.testalbum, self.testalbum.id,
                                  AnonymousUser(), album.display_album, ALBUM_PUBLIC)

        # test photo view
        self.perm_escalate_helper(self.albumcontrol, self.photorequest, self.testalbum, self.photo.id,
                                  AnonymousUser(), album.return_photo_file_http, ALBUM_PUBLIC)

        # test individual photo view page
        self.perm_escalate_helper(self.albumcontrol, self.indivphotorequest, self.testalbum, self.photo.id,
                                  AnonymousUser(), album.display_photo, ALBUM_PUBLIC)

    def test_logged_in_not_friend(self):
        """
        Logged in not friend has same permissions as non logged in user
        """

        # log in
        self.make_logged_in_not_friend()

        # test show album
        self.perm_escalate_helper(self.albumcontrol, self.showalbumrequest, self.testalbum, self.testalbum.id,
                                  self.u2, album.display_album, ALBUM_PUBLIC)

        # test photo view
        self.perm_escalate_helper(self.albumcontrol, self.photorequest, self.testalbum, self.photo.id,
                                  self.u2, album.return_photo_file_http, ALBUM_PUBLIC)

        # test individual photo view page
        self.perm_escalate_helper(self.albumcontrol, self.indivphotorequest, self.testalbum, self.photo.id,
                                  self.u2, album.display_photo, ALBUM_PUBLIC)

    def test_logged_in_friend_not_in_group(self):
        """
        Logged in friend not in group should be able to access ALL_FRIENDS permission
        """

        self.make_logged_in_friend_not_in_group()

        # test show album
        self.perm_escalate_helper(self.albumcontrol, self.showalbumrequest, self.testalbum, self.testalbum.id,
                                  self.u2, album.display_album, ALBUM_ALLFRIENDS)

        # test photo view
        self.perm_escalate_helper(self.albumcontrol, self.photorequest, self.testalbum, self.photo.id,
                                  self.u2, album.return_photo_file_http, ALBUM_ALLFRIENDS)

        # test individual photo view page
        self.perm_escalate_helper(self.albumcontrol, self.indivphotorequest, self.testalbum, self.photo.id,
                                  self.u2, album.display_photo, ALBUM_ALLFRIENDS)

    def test_logged_in_friend_in_group(self):
        """
        Logged in friend in group should be able to access GROUPS permission
        """
        self.make_logged_in_friend_in_group()

        # test show album
        self.perm_escalate_helper(self.albumcontrol, self.showalbumrequest, self.testalbum, self.testalbum.id,
                                  self.u2, album.display_album, ALBUM_GROUPS)

        # test photo view
        self.perm_escalate_helper(self.albumcontrol, self.photorequest, self.testalbum, self.photo.id,
                                  self.u2, album.return_photo_file_http, ALBUM_GROUPS)

        # test individual photo view page
        self.perm_escalate_helper(self.albumcontrol, self.indivphotorequest, self.testalbum, self.photo.id,
                                  self.u2, album.display_photo, ALBUM_GROUPS)

    def test_logged_in_contributor(self):
        """
        Contributor can access PRIVATE permission
        """
        self.make_logged_in_contributor()

        # test show album
        self.perm_escalate_helper(self.albumcontrol, self.showalbumrequest, self.testalbum, self.testalbum.id,
                                  self.u2, album.display_album, ALBUM_PRIVATE)

        # test photo view
        self.perm_escalate_helper(self.albumcontrol, self.photorequest, self.testalbum, self.photo.id,
                                  self.u2, album.return_photo_file_http, ALBUM_PRIVATE)

        # test individual photo view page
        self.perm_escalate_helper(self.albumcontrol, self.indivphotorequest, self.testalbum, self.photo.id,
                                  self.u2, album.display_photo, ALBUM_PRIVATE)

    def test_logged_in_owner(self):
        """
        Login as album creator (owner) and access all access types
        """
        self.make_logged_in_owner()

        # test show album
        self.perm_escalate_helper(self.albumcontrol, self.showalbumrequest, self.testalbum, self.testalbum.id,
                                  self.u, album.display_album, ALBUM_PRIVATE)

        # test photo view
        self.perm_escalate_helper(self.albumcontrol, self.photorequest, self.testalbum, self.photo.id,
                                  self.u, album.return_photo_file_http, ALBUM_PRIVATE)

        # test individual photo view page
        self.perm_escalate_helper(self.albumcontrol, self.indivphotorequest, self.testalbum, self.photo.id,
                                  self.u, album.display_photo, ALBUM_PRIVATE)


class test_manage_page_permissions(PermissionTestCase):
    def setUp(self):
        super(test_manage_page_permissions, self).setUp()
        # view manage page
        self.managepagerequest = self.factory.get(reverse("manage_album", kwargs={'albumid': self.testalbum.id}))

    def test_get_(self):
        pass
    def test_post_(self):
        pass


class test_upload_photo_permissions(PermissionTestCase):
    def setUp(self):
        super(test_upload_photo_permissions, self).setUp()

        self.uploadphotorequest = self.factory.get(reverse("upload_photos", kwargs={'id': self.testalbum.id}))
        # todo: add post upload photo request

    def test_not_logged_in(self):
        # can't add photos to album
        # assign anonymous user to request
        self.uploadphotorequest.user = AnonymousUser()

        self.albumcontrol.set_accesstype(self.testalbum, ALBUM_PUBLIC)

        response = album.add_photo(self.uploadphotorequest, self.testalbum.id)
        # since we are not logged in, redirects to login page
        assert response.status_code == 302
        # may be good to add a post test for upload_photos, even though we have login_required decorator
        # just to have complete coverage

    def test_logged_in_not_friend(self):
        self.make_logged_in_not_friend()

        # test get upload photo page
        self.uploadphotorequest.user = self.u2
        self.albumcontrol.set_accesstype(self.testalbum, ALBUM_PUBLIC)

        self.assertRaises(PermissionException, album.add_photo, self.uploadphotorequest, self.testalbum.id)

    def test_logged_in_friend_not_in_group(self):
        self.make_logged_in_friend_not_in_group()


class test_change_album_accesstype(PermissionTestCase):
    """
    Only owner can edit album access type
    """
    def setUp(self):
        #self.updateaccesstyperequest = self.factory.post(reverse("update_album_access"))
        pass


class test_add_remove_album_contrib(PermissionTestCase):
    """
    Only owner can edit contributors
    """
    def setUp(self):
        super(test_add_remove_album_contrib, self).setUp()
        self.addcontribpostrequest = self.factory.post(reverse("add_album_contrib", kwargs={"albumid": self.testalbum.id}))

    def test_get(self):
        """
        Get will return a 404 under all conditions
        """
        self.addcontribgetrequest = self.factory.get(
            reverse("add_album_contrib", kwargs={"albumid": self.testalbum.id}))
        self.addcontribgetrequest.user = self.u

        assert album.add_contrib(self.addcontribgetrequest, self.testalbum.id) == Http404

class test_add_remove_groups(PermissionTestCase):
    """
    Contributor can add/remove own groups if access type is groups
    Owner can add/remove own groups
    """
    # todo: think about what if owner doesn't want contributors to add groups
    def setUp(self):
        #self.addgrouprequest = self.factory.post(reverse("add_album_groups"))
        pass
